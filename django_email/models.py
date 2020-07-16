from django.contrib.postgres.fields import JSONField, ArrayField
from django.db import models
from django.db.models import F
from .abstract_models import AbstractModel
from .constants import EMAIL_PROVIDER_CHOICES


class EmailLog(AbstractModel):

    EMAIL_STATUS_QUEUED = "queued"
    EMAIL_STATUS_SENT = "sent"
    EMAIL_STATUS_FAILED = "failed"

    EMAIL_DISPATCH_STATUS_CHOICES = (
        (EMAIL_STATUS_SENT, "Sent"),
        (EMAIL_STATUS_QUEUED, "Queued"),
        (EMAIL_STATUS_FAILED, "Failed"),
    )

    email_provider = models.CharField(
        max_length=32,
        choices=EMAIL_PROVIDER_CHOICES,
        help_text="Name of the email provider used to send email",
    )

    from_email = models.EmailField(help_text="Email address of the sender")
    from_name = models.CharField(max_length=200, null=True, blank=True, help_text="Name of the sender")
    to_emails = ArrayField(
        models.EmailField(), help_text="List of email addresses of primary recipients",
    )
    cc_emails = ArrayField(
        models.EmailField(),
        null=True,
        help_text="List of email addresses of cc'ed recipients",
    )
    bcc_emails = ArrayField(
        models.EmailField(),
        null=True,
        help_text="List of email addresses of bcc'ed recipients",
    )

    subject = models.TextField(help_text="Subject of the email")
    body = models.TextField(null=True, help_text="Body of the email")
    template_id = models.CharField(
        max_length=64,
        null=True,
        help_text="Template Id of the template used to send email",
    )
    template_dynamic_data = JSONField(
        null=True,
        help_text="Dictionary containing values for " "dynamic variables in template",
    )

    dispatch_status = models.CharField(
        max_length=16,
        choices=EMAIL_DISPATCH_STATUS_CHOICES,
        default=EMAIL_STATUS_QUEUED,
        help_text="Status of the message whether it is not sent or sent",
    )

    error_info = JSONField(
        null=True, help_text="Details of error when message sending is failed"
    )

    reply_to = models.EmailField(null=True, blank=True, help_text="The Reply-to email address")

    def __str__(self):
        return f"To: {self.to_emails} Subject:{self.subject}"

    @classmethod
    def create_log(
        cls,
        email_provider,
        from_email,
        from_name,
        to_emails,
        cc_emails,
        bcc_emails,
        subject,
        body,
        template_id,
        template_dynamic_data,
        reply_to,
    ):
        email_log = cls.objects.create(
            email_provider=email_provider,
            from_email=from_email,
            from_name=from_name,
            to_emails=to_emails,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails,
            subject=subject,
            body=body,
            template_id=template_id,
            template_dynamic_data=template_dynamic_data,
            reply_to=reply_to
        )

        return email_log


class EmailActivityTracker(AbstractModel):
    TO_RECIPIENT_TYPE = "to"
    CC_RECIPIENT_TYPE = "cc"
    BCC_RECIPIENT_TYPE = "bcc"

    RECIPIENT_TYPE_CHOICES = (
        (TO_RECIPIENT_TYPE, "To"),
        (CC_RECIPIENT_TYPE, "Cc"),
        (BCC_RECIPIENT_TYPE, "Bcc"),
    )

    SENT_EMAIL_STATUS_QUEUED = "queued"
    SENT_EMAIL_STATUS_DELIVERED = "delivered"
    SENT_EMAIL_STATUS_SPAMMED = "spammed"
    SENT_EMAIL_STATUS_SOFT_BOUNCED = "soft_bounced"
    SENT_EMAIL_STATUS_HARD_BOUNCED = "hard_bounced"

    SENT_EMAIL_STATUS_CHOICES = (
        (SENT_EMAIL_STATUS_QUEUED, "Queued"),
        (SENT_EMAIL_STATUS_DELIVERED, "Delivered"),
        (SENT_EMAIL_STATUS_SPAMMED, "Spammed"),
        (SENT_EMAIL_STATUS_SOFT_BOUNCED, "Soft Bounced"),
        (SENT_EMAIL_STATUS_HARD_BOUNCED, "Hard Bounced"),
    )

    email_log = models.ForeignKey(
        EmailLog,
        on_delete=models.PROTECT,
        help_text="Email info of the email which is being tracked",
    )
    recipient_type = models.CharField(
        max_length=3,
        choices=RECIPIENT_TYPE_CHOICES,
        help_text="Type of recipient to whom this email was sent",
    )
    email_address = models.EmailField(help_text="Email address of the recipient")

    message_id = models.CharField(
        max_length=128,
        unique=True,
        help_text="Unique identifier of the message which is being tracked",
    )

    open_count = models.IntegerField(default=0, help_text="Open count of the email")
    click_count = models.IntegerField(default=0, help_text="Click count of the email")

    email_status = models.CharField(
        max_length=16,
        choices=SENT_EMAIL_STATUS_CHOICES,
        default=SENT_EMAIL_STATUS_QUEUED,
        help_text="Status of the email after it is dispatched.",
    )

    def __str__(self):
        return self.email_address

    @classmethod
    def get_by_message_id(cls, message_id):
        try:
            return cls.objects.get(message_id=message_id)
        except cls.DoesNotExist:
            return None

    @classmethod
    def track_recipient(cls, recipient_data: dict):
        cls.objects.create(**recipient_data)

    def update_fields_on_event(self, event_type):
        event_type_vs_update_fields = {
            EventLog.EMAIL_OPENED_EVENT_TYPE: {"open_count": F("open_count") + 1},
            EventLog.EMAIL_CLICKED_EVENT_TYPE: {"click_count": F("click_count") + 1},
            EventLog.EMAIL_DELIVERED_EVENT_TYPE: {
                "email_status": EmailActivityTracker.SENT_EMAIL_STATUS_DELIVERED
            },
            EventLog.EMAIL_SOFT_BOUNCED_EVENT_TYPE: {
                "email_status": EmailActivityTracker.SENT_EMAIL_STATUS_SOFT_BOUNCED
            },
            EventLog.EMAIL_HARD_BOUNCED_EVENT_TYPE: {
                "email_status": EmailActivityTracker.SENT_EMAIL_STATUS_HARD_BOUNCED
            },
        }

        self.update_fields(**event_type_vs_update_fields[event_type])


class EventLog(AbstractModel):
    EMAIL_DELIVERED_EVENT_TYPE = "delivered"
    EMAIL_OPENED_EVENT_TYPE = "opened"
    EMAIL_CLICKED_EVENT_TYPE = "clicked"
    EMAIL_SPAMMED_EVENT_TYPE = "spammed"
    EMAIL_SOFT_BOUNCED_EVENT_TYPE = "soft_bounced"
    EMAIL_HARD_BOUNCED_EVENT_TYPE = "hard_bounced"

    EVENT_TYPE_CHOICES = (
        (EMAIL_DELIVERED_EVENT_TYPE, "Delivered"),
        (EMAIL_OPENED_EVENT_TYPE, "Opened"),
        (EMAIL_CLICKED_EVENT_TYPE, "Clicked"),
        (EMAIL_SPAMMED_EVENT_TYPE, "Spammed"),
        (EMAIL_SOFT_BOUNCED_EVENT_TYPE, "Soft Bounced"),
        (EMAIL_HARD_BOUNCED_EVENT_TYPE, "Hard bounced"),
    )

    email_activity_tracker = models.ForeignKey(
        EmailActivityTracker,
        on_delete=models.PROTECT,
        help_text="The email log to which this event belongs to",
    )
    event_type = models.CharField(
        max_length=16,
        choices=EVENT_TYPE_CHOICES,
        help_text="Type of the event which is being logged",
    )
    event_info = JSONField(help_text="Stores info about the event")

    event_at = models.DateTimeField(help_text="The time at which this event occurred")

    def __str__(self):
        return f"{self.event_at}: {self.event_type}"

    @classmethod
    def add_new_event_log(cls, event_info):
        return cls.objects.create(**event_info)
