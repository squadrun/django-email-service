import json
from unittest import mock

from django.urls import reverse
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from ..constants import EMAIL_PROVIDER_MAILJET
from ..services import EmailService


class EmailEventWebhookViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_email_event_webhook_view_POST(self):
        email_provider = EMAIL_PROVIDER_MAILJET
        event_webhook_url = reverse(
            "email_event_webhook", kwargs={"email_provider": email_provider}
        )
        event_info_dict = {"event": "sent"}
        event_info_json = json.loads(json.dumps(event_info_dict))

        with mock.patch('django_email.views.handle_webhook.apply_async') as mocked_handle_event_webhook:
            response = self.client.post(
                event_webhook_url, event_info_json, format="json"
            )

            mocked_handle_event_webhook.assert_called_with(
                ('{"event":"sent"}', email_provider)
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
