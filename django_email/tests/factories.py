import factory
import pytz
from factory.django import DjangoModelFactory
from faker import Factory

from ..constants import EMAIL_PROVIDER_CHOICES
from ..models import EmailLog, EmailActivityTracker, EventLog

faker = Factory.create()


class EmailLogFactory(DjangoModelFactory):
    class Meta:
        model = EmailLog

    email_provider = factory.LazyAttribute(
        lambda _: faker.random_choices(elements=[x[0] for x in EMAIL_PROVIDER_CHOICES])[
            0
        ]
    )
    from_email = factory.LazyAttribute(lambda _: faker.email())
    from_name = factory.LazyAttribute(lambda _: faker.name())
    to_emails = factory.LazyAttribute(lambda _: [faker.email()])
    cc_emails = factory.LazyAttribute(lambda _: [faker.email()])
    bcc_emails = factory.LazyAttribute(lambda _: [faker.email()])
    subject = factory.LazyAttribute(lambda _: [faker.text(max_nb_chars=20)])
    body = factory.LazyAttribute(lambda _: [faker.text(max_nb_chars=40)])


class EmailActivityTrackerFactory(DjangoModelFactory):
    class Meta:
        model = EmailActivityTracker

    email_log = factory.SubFactory(EmailLogFactory)
    recipient_type = EmailActivityTracker.TO_RECIPIENT_TYPE
    email_address = factory.LazyAttribute(lambda _: faker.email())
    message_id = factory.LazyAttribute(lambda _: faker.uuid4())


class EventLogFactory(DjangoModelFactory):
    class Meta:
        model = EventLog

    email_activity_tracker = factory.SubFactory(EmailActivityTrackerFactory)
    event_type = factory.LazyAttribute(
        lambda _: faker.random_choices(
            elements=[x[0] for x in EventLog.EVENT_TYPE_CHOICES]
        )[0]
    )
    event_at = factory.LazyAttribute(lambda _: faker.date_time(tzinfo=pytz.utc))
    event_info = {"event": "sent"}
