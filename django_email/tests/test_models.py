from datetime import datetime

import pytz
from django.conf import settings
from django.test import TestCase

from ..constants import DEFAULT_EMAIL_PROVIDER
from ..models import EmailLog, EmailActivityTracker, EventLog
from ..tests.factories import (
    EmailLogFactory,
    EmailActivityTrackerFactory,
)


class EmailLogModelTestCase(TestCase):
    def test_create_log(self):

        email_provider = DEFAULT_EMAIL_PROVIDER
        from_email = settings.DEFAULT_FROM_NAME
        from_name = "Tony Stark"
        to_emails = ["to_email@example.com"]
        cc_emails = ["cc_email@example.com"]
        bcc_emails = ["bcc_email@example.com"]
        subject = "Test Email"
        body = "Test body"
        template_id = "12345678"
        template_dynamic_data = {"name": "example_name"}

        email_log = EmailLog.create_log(
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
        )
        self.assertTupleEqual(
            (
                email_log.email_provider,
                email_log.from_email,
                email_log.to_emails,
                email_log.cc_emails,
                email_log.bcc_emails,
                email_log.subject,
                email_log.body,
                email_log.template_id,
                email_log.template_dynamic_data,
                email_log.dispatch_status,
            ),
            (
                email_provider,
                from_email,
                to_emails,
                cc_emails,
                bcc_emails,
                subject,
                body,
                template_id,
                template_dynamic_data,
                EmailLog.EMAIL_STATUS_QUEUED,
            ),
        )


class EmailActivityTrackerModelTestCase(TestCase):
    def setUp(self):
        self.email_log = EmailLogFactory()
        self.email_activity_tracker = EmailActivityTrackerFactory()

    def test_get_by_message_id(self):
        message_id = "test_message_id"
        self.assertIsNone(EmailActivityTracker.get_by_message_id(message_id))

        self.assertEqual(
            self.email_activity_tracker,
            EmailActivityTracker.get_by_message_id(
                self.email_activity_tracker.message_id
            ),
        )

    def test_track_recipient(self):
        recipient_data = {
            "email_log": self.email_log,
            "recipient_type": EmailActivityTracker.TO_RECIPIENT_TYPE,
            "email_address": "noreply@example.com",
            "message_id": "123456789",
        }

        EmailActivityTracker.track_recipient(recipient_data)
        email_activity_tracker = EmailActivityTracker.get_by_message_id(
            recipient_data["message_id"]
        )
        self.assertTupleEqual(
            (
                email_activity_tracker.email_log,
                email_activity_tracker.recipient_type,
                email_activity_tracker.email_address,
                email_activity_tracker.message_id,
                email_activity_tracker.email_status,
                email_activity_tracker.open_count,
                email_activity_tracker.click_count,
            ),
            (
                recipient_data["email_log"],
                recipient_data["recipient_type"],
                recipient_data["email_address"],
                recipient_data["message_id"],
                EmailActivityTracker.SENT_EMAIL_STATUS_QUEUED,
                0,
                0,
            ),
        )

    def test_update_fields_on_open_event(self):
        old_open_count = self.email_activity_tracker.open_count

        self.email_activity_tracker.update_fields_on_event(
            EventLog.EMAIL_OPENED_EVENT_TYPE
        )
        self.email_activity_tracker.refresh_from_db()

        self.assertEqual(self.email_activity_tracker.open_count, old_open_count + 1)

    def test_update_fields_on_click_event(self):
        old_click_count = self.email_activity_tracker.click_count

        self.email_activity_tracker.update_fields_on_event(
            EventLog.EMAIL_CLICKED_EVENT_TYPE
        )
        self.email_activity_tracker.refresh_from_db()

        self.assertEqual(self.email_activity_tracker.click_count, old_click_count + 1)

    def test_update_fields_on_sent_event(self):
        self.email_activity_tracker.update_fields_on_event(
            EventLog.EMAIL_DELIVERED_EVENT_TYPE
        )

        self.assertEqual(
            self.email_activity_tracker.email_status,
            EmailActivityTracker.SENT_EMAIL_STATUS_DELIVERED,
        )

    def test_update_fields_on_soft_bounced_event(self):
        self.email_activity_tracker.update_fields_on_event(
            EventLog.EMAIL_SOFT_BOUNCED_EVENT_TYPE
        )

        self.assertEqual(
            self.email_activity_tracker.email_status,
            EmailActivityTracker.SENT_EMAIL_STATUS_SOFT_BOUNCED,
        )

    def test_update_fields_on_hard_bounced(self):
        self.email_activity_tracker.update_fields_on_event(
            EventLog.EMAIL_HARD_BOUNCED_EVENT_TYPE
        )

        self.assertEqual(
            self.email_activity_tracker.email_status,
            EmailActivityTracker.SENT_EMAIL_STATUS_HARD_BOUNCED,
        )


class EventLogModelTestCase(TestCase):
    def setUp(self):
        self.email_activity_tracker = EmailActivityTrackerFactory()

    def test_add_new_event_log(self):
        event_data = {
            "email_activity_tracker": self.email_activity_tracker,
            "event_at": pytz.UTC.localize(datetime.now()),
            "event_type": EventLog.EMAIL_DELIVERED_EVENT_TYPE,
            "event_info": {"event": "delivered"},
        }

        EventLog.add_new_event_log(event_data)
        event_log = EventLog.objects.get(
            email_activity_tracker=self.email_activity_tracker,
            event_at=event_data["event_at"],
        )

        self.assertTupleEqual(
            (event_log.event_type, event_log.event_info),
            (event_data["event_type"], event_data["event_info"]),
        )
