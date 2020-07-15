from unittest import mock

from django.test import TestCase
from django.conf import settings

from ..constants import EMAIL_PROVIDER_MAILJET
from ..models import EmailLog
from ..providers.mailjet import MailjetEmailProvider
from ..services import EmailService
from ..tests.factories import EmailLogFactory


class EmailServiceTestCase(TestCase):
    def test_get_provider_class_for_provider(self):
        provider = EMAIL_PROVIDER_MAILJET
        provider_class = EmailService._get_provider_class_for_provider(provider)

        self.assertEqual(provider_class, MailjetEmailProvider)

        provider = "test_provider"
        with self.assertRaises(ValueError):
            EmailService._get_provider_class_for_provider(provider)

    def test_send_email_of_mailjet(self):
        to_emails = ["to_email@example.com"]
        cc_emails = ["cc_email@example.com"]
        bcc_emails = ["bcc_email@example.com"]
        subject = "Test Email"
        response = {"MessageId": "123456"}
        body = "test body"
        template_id = "test_template_id"
        template_dynamic_data = {"name": "test_name"}
        email_log = EmailLogFactory()
        from_email = settings.DEFAULT_FROM_EMAIL
        from_name = settings.DEFAULT_FROM_NAME
        email_provider = EMAIL_PROVIDER_MAILJET

        with mock.patch.object(
            EmailService, "_get_provider_class_for_provider"
        ) as mocked_get_provider_class_for_provider, mock.patch.object(
            EmailLog, "create_log"
        ) as mocked_create_log, mock.patch.object(
            MailjetEmailProvider, "send_email"
        ) as mocked_mailjet_send_email, mock.patch.object(
            MailjetEmailProvider, "handle_send_email_response"
        ) as mocked_handle_send_email_response:
            mocked_get_provider_class_for_provider.return_value = MailjetEmailProvider
            mocked_create_log.return_value = email_log
            mocked_mailjet_send_email.return_value = response

            EmailService.send_email(
                to_emails,
                subject,
                cc_emails,
                bcc_emails,
                body,
                template_id,
                template_dynamic_data,
                from_email,
                from_name,
                email_provider,
            )

            mocked_get_provider_class_for_provider.assert_called_with(email_provider)
            mocked_create_log.assert_called_with(
                EMAIL_PROVIDER_MAILJET,
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
            mocked_mailjet_send_email.assert_called_with(email_log)
            mocked_handle_send_email_response.called_with(response, email_log)

    def test_handle_event_webhook_of_mailjet(self):
        event_info = {"event": "sent"}

        with mock.patch.object(
            EmailService, "_get_provider_class_for_provider"
        ) as mocked_get_provider_class, mock.patch.object(
            MailjetEmailProvider, "handle_event_webhook"
        ) as mocked_mailjet_handle_event_webhook:
            mocked_get_provider_class.return_value = MailjetEmailProvider

            EmailService.handle_event_webhook(EMAIL_PROVIDER_MAILJET, event_info)

            mocked_get_provider_class.assert_called_with(EMAIL_PROVIDER_MAILJET)
            mocked_mailjet_handle_event_webhook.assert_called_with(event_info)
