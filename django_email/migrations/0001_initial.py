# Generated by Django 3.0.5 on 2020-05-22 10:57

import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EmailActivityTracker",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        editable=False,
                        help_text="Time of creation of this object",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, help_text="Time of updation of this object"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Denotes if the object is active or not."
                        "Inactive objects behave similar to how a deleted object works.",
                    ),
                ),
                (
                    "recipient_type",
                    models.CharField(
                        choices=[("to", "To"), ("cc", "Cc"), ("bcc", "Bcc")],
                        help_text="Type of recipient to whom this email was sent",
                        max_length=3,
                    ),
                ),
                (
                    "email_address",
                    models.EmailField(
                        help_text="Email address of the recipient", max_length=254
                    ),
                ),
                (
                    "message_id",
                    models.CharField(
                        help_text="Unique identifier of the message which is being tracked",
                        max_length=128,
                        unique=True,
                    ),
                ),
                (
                    "open_count",
                    models.IntegerField(default=0, help_text="Open count of the email"),
                ),
                (
                    "click_count",
                    models.IntegerField(
                        default=0, help_text="Click count of the email"
                    ),
                ),
                (
                    "email_status",
                    models.CharField(
                        choices=[
                            ("queued", "Queued"),
                            ("delivered", "Delivered"),
                            ("spammed", "Spammed"),
                            ("soft_bounced", "Soft Bounced"),
                            ("hard_bounced", "Hard Bounced"),
                        ],
                        default="queued",
                        help_text="Status of the email after it is dispatched.",
                        max_length=16,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="EmailLog",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        editable=False,
                        help_text="Time of creation of this object",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, help_text="Time of updation of this object"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Denotes if the object is active or not."
                        "Inactive objects behave similar to how a deleted object works.",
                    ),
                ),
                (
                    "email_provider",
                    models.CharField(
                        choices=[("mailjet", "Mailjet")],
                        help_text="Name of the email provider used to send email",
                        max_length=32,
                    ),
                ),
                (
                    "from_email",
                    models.EmailField(
                        help_text="Email address of the sender", max_length=254
                    ),
                ),
                (
                    "to_emails",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.EmailField(max_length=254),
                        help_text="List of email addresses of primary recipients",
                        size=None,
                    ),
                ),
                (
                    "cc_emails",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.EmailField(max_length=254),
                        help_text="List of email addresses of cc'ed recipients",
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "bcc_emails",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.EmailField(max_length=254),
                        help_text="List of email addresses of bcc'ed recipients",
                        null=True,
                        size=None,
                    ),
                ),
                ("subject", models.TextField(help_text="Subject of the email")),
                ("body", models.TextField(help_text="Body of the email", null=True)),
                (
                    "template_id",
                    models.CharField(
                        help_text="Template Id of the template used to send email",
                        max_length=64,
                        null=True,
                    ),
                ),
                (
                    "template_dynamic_data",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        help_text="Dictionary containing values for dynamic variables in template",
                        null=True,
                    ),
                ),
                (
                    "dispatch_status",
                    models.CharField(
                        choices=[
                            ("sent", "Sent"),
                            ("queued", "Queued"),
                            ("failed", "Failed"),
                        ],
                        default="queued",
                        help_text="Status of the message whether it is not sent or sent",
                        max_length=16,
                    ),
                ),
                (
                    "error_info",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        help_text="Details of error when message sending is failed",
                        null=True,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="EventLog",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        editable=False,
                        help_text="Time of creation of this object",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, help_text="Time of updation of this object"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Denotes if the object is active or not."
                        "Inactive objects behave similar to how a deleted object works.",
                    ),
                ),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("delivered", "Delivered"),
                            ("opened", "Opened"),
                            ("clicked", "Clicked"),
                            ("spammed", "Spammed"),
                            ("soft_bounced", "Soft Bounced"),
                            ("hard_bounced", "Hard bounced"),
                        ],
                        help_text="Type of the event which is being logged",
                        max_length=16,
                    ),
                ),
                (
                    "event_info",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        help_text="Stores info about the event"
                    ),
                ),
                (
                    "event_at",
                    models.DateTimeField(
                        help_text="The time at which this event occurred"
                    ),
                ),
                (
                    "email_activity_tracker",
                    models.ForeignKey(
                        help_text="The email log to which this event belongs to",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="django_email.EmailActivityTracker",
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.AddIndex(
            model_name="emaillog",
            index=models.Index(
                condition=models.Q(is_active=True),
                fields=["is_active"],
                name="emaillog_is_active",
            ),
        ),
        migrations.AddField(
            model_name="emailactivitytracker",
            name="email_log",
            field=models.ForeignKey(
                help_text="Email info of the email which is being tracked",
                on_delete=django.db.models.deletion.PROTECT,
                to="django_email.EmailLog",
            ),
        ),
        migrations.AddIndex(
            model_name="eventlog",
            index=models.Index(
                condition=models.Q(is_active=True),
                fields=["is_active"],
                name="eventlog_is_active",
            ),
        ),
        migrations.AddIndex(
            model_name="emailactivitytracker",
            index=models.Index(
                condition=models.Q(is_active=True),
                fields=["is_active"],
                name="emailactivitytracker_is_active",
            ),
        ),
    ]