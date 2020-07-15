from django.test import TestCase
from django.urls import resolve, reverse

from ..constants import EMAIL_PROVIDER_MAILJET
from ..views import EmailEventWebhookView


class TestUrls(TestCase):
    def test_email_event_webhook_view(self):
        url = reverse(
            "email_event_webhook", kwargs={"email_provider": EMAIL_PROVIDER_MAILJET}
        )
        self.assertEqual(resolve(url).func.view_class, EmailEventWebhookView)
