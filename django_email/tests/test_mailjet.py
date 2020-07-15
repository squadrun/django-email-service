import json
from datetime import datetime
from unittest import mock

import pytz
from django.test import TestCase
from requests.models import Response
from rest_framework import status

from ..exceptions import EmailActivityTrackerNotFoundException
from ..models import EmailActivityTracker, EmailLog, EventLog
from ..providers.mailjet import MailjetEmailProvider
from ..tests.factories import (
    EmailLogFactory,
    EmailActivityTrackerFactory,
    EventLogFactory,
)


class MailjetEmailProviderTestCase(TestCase):
    def setUp(self):
        self.email_log = EmailLogFactory()
        self.email_activity_tracker = EmailActivityTrackerFactory()
        self.event_log = EventLogFactory()

    def test_create_email_data(self):
        data = {
            "Messages": [
                {
                    "From": {"Email": self.email_log.from_email, "Name": self.email_log.from_name},
                    "To": [{"Email": self.email_log.to_emails[0]}],
                    "Cc": [{"Email": self.email_log.cc_emails[0]}],
                    "Bcc": [{"Email": self.email_log.bcc_emails[0]}],
                    "Subject": self.email_log.subject,
                    "HTMLPart": self.email_log.body,
                }
            ]
        }

        self.assertEqual(MailjetEmailProvider._create_email_data(self.email_log), data)

    def test_create_email_data_with_template(self):
        self.email_log.update_fields(
            body=None,
            cc_emails=None,
            bcc_emails=None,
            template_id="test_id",
            template_dynamic_data={"variable": "test_variable"},
        )

        data = {
            "Messages": [
                {
                    "From": {"Email": self.email_log.from_email, "Name": self.email_log.from_name},
                    "To": [{"Email": self.email_log.to_emails[0]}],
                    "Subject": self.email_log.subject,
                    "TemplateID": self.email_log.template_id,
                    "TemplateLanguage": True,
                    "Variables": self.email_log.template_dynamic_data,
                }
            ]
        }

        self.assertDictEqual(
            MailjetEmailProvider._create_email_data(self.email_log), data
        )

    def test_parse_sent_email_response_for_email_log(self):
        api_sent_email_response = {
            "Messages": [
                {
                    "Status": "success",
                    "To": [
                        {
                            "Email": "passenger1@mailjet.com",
                            "MessageUUID": "123",
                            "MessageID": 456,
                            "MessageHref": "https://api.mailjet.com/v3/message/456",
                        },
                    ],
                    "Cc": [
                        {
                            "Email": "copilot@mailjet.com",
                            "MessageUUID": "125",
                            "MessageID": 458,
                            "MessageHref": "https://api.mailjet.com/v3/message/458",
                        }
                    ],
                    "Bcc": [
                        {
                            "Email": "air-traffic-control@mailjet.com",
                            "MessageUUID": "126",
                            "MessageID": 459,
                            "MessageHref": "https://api.mailjet.com/v3/message/459",
                        }
                    ],
                }
            ]
        }

        parsed_sent_email_response = [
            {
                "recipient_type": EmailActivityTracker.TO_RECIPIENT_TYPE,
                "email_address": "passenger1@mailjet.com",
                "message_id": str(456),
            },
            {
                "recipient_type": EmailActivityTracker.CC_RECIPIENT_TYPE,
                "email_address": "copilot@mailjet.com",
                "message_id": str(458),
            },
            {
                "recipient_type": EmailActivityTracker.BCC_RECIPIENT_TYPE,
                "email_address": "air-traffic-control@mailjet.com",
                "message_id": str(459),
            },
        ]

        sent_email_response = Response()
        sent_email_response._content = json.dumps(api_sent_email_response).encode(
            "utf-8"
        )
        sent_email_response.status_code = status.HTTP_200_OK

        self.assertTupleEqual(
            MailjetEmailProvider.parse_send_email_response_for_email_log(
                sent_email_response
            ),
            (EmailLog.EMAIL_STATUS_SENT, parsed_sent_email_response),
        )

    def test_parse_send_email_error_response_for_email_log(self):
        api_send_email_error_response = {
            "Messages": [
                {
                    "Status": "success",
                    "Errors": [
                        {
                            "ErrorIdentifier": "1ab23cd4-e567-8901-2345-6789f0gh1i2j",
                            "ErrorCode": "send-0010",
                            "StatusCode": 400,
                            "ErrorMessage": 'Template ID "123456789" doesn\'t exist for your account.',
                            "ErrorRelatedTo": "TemplateID",
                        }
                    ],
                }
            ]
        }

        parsed_send_email_error_response = {
            "error": {
                "Messages": [
                    {
                        "Status": "success",
                        "Errors": [
                            {
                                "ErrorIdentifier": "1ab23cd4-e567-8901-2345-6789f0gh1i2j",
                                "ErrorCode": "send-0010",
                                "StatusCode": 400,
                                "ErrorMessage": 'Template ID "123456789" doesn\'t exist for your account.',
                                "ErrorRelatedTo": "TemplateID",
                            }
                        ],
                    }
                ]
            }
        }

        send_email_error_response = Response()
        send_email_error_response._content = json.dumps(
            api_send_email_error_response
        ).encode("utf-8")
        send_email_error_response.status_code = status.HTTP_400_BAD_REQUEST

        self.assertTupleEqual(
            MailjetEmailProvider.parse_send_email_response_for_email_log(
                send_email_error_response
            ),
            (EmailLog.EMAIL_STATUS_FAILED, parsed_send_email_error_response),
        )

    def test_parse_event_webhook_for_email_sent(self):
        event_info = {
            "event": "sent",
            "time": 1433103519,
            "MessageID": 19421777396190490,
            "Message_GUID": "1ab23cd4-e567-8901-2345-6789f0gh1i2j",
            "email": "api@mailjet.com",
            "mj_campaign_id": 7173,
            "mj_contact_id": 320,
            "customcampaign": "",
            "CustomID": "helloworld",
            "Payload": "",
            "ip": "127.0.0.1",
            "geo": "US",
            "agent": "Mozilla/5.0 (Windows NT 5.1; rv:11.0) Gecko Firefox/11.0",
        }

        parsed_event_info = {
            "event_at": pytz.UTC.localize(
                datetime.utcfromtimestamp(event_info["time"])
            ),
            "event_info": event_info,
            "event_type": EventLog.EMAIL_DELIVERED_EVENT_TYPE,
        }

        self.assertTupleEqual(
            MailjetEmailProvider.parse_event_webhook(event_info),
            (str(event_info["MessageID"]), parsed_event_info),
        )

    def test_parse_event_webhook_for_email_opened(self):
        event_info = {
            "event": "open",
            "time": 1433103519,
            "MessageID": 19421777396190490,
            "Message_GUID": "1ab23cd4-e567-8901-2345-6789f0gh1i2j",
            "email": "api@mailjet.com",
            "mj_campaign_id": 7173,
            "mj_contact_id": 320,
            "customcampaign": "",
            "CustomID": "helloworld",
            "Payload": "",
            "ip": "127.0.0.1",
            "geo": "US",
            "agent": "Mozilla/5.0 (Windows NT 5.1; rv:11.0) Gecko Firefox/11.0",
        }

        parsed_event_info = {
            "event_at": pytz.UTC.localize(
                datetime.utcfromtimestamp(event_info["time"])
            ),
            "event_info": event_info,
            "event_type": EventLog.EMAIL_OPENED_EVENT_TYPE,
        }

        self.assertTupleEqual(
            MailjetEmailProvider.parse_event_webhook(event_info),
            (str(event_info["MessageID"]), parsed_event_info),
        )

    def test_parse_event_webhook_for_email_clicked_event(self):
        event_info = {
            "event": "click",
            "time": 1433334653,
            "MessageID": 19421777836302490,
            "Message_GUID": "1ab23cd4-e567-8901-2345-6789f0gh1i2j",
            "email": "api@mailjet.com",
            "mj_campaign_id": 7272,
            "mj_contact_id": 4,
            "customcampaign": "",
            "CustomID": "helloworld",
            "Payload": "",
            "url": "https://mailjet.com",
            "ip": "127.0.0.1",
            "geo": "FR",
            "agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36",
        }

        parsed_event_info = {
            "event_at": pytz.UTC.localize(
                datetime.utcfromtimestamp(event_info["time"])
            ),
            "event_info": event_info,
            "event_type": EventLog.EMAIL_CLICKED_EVENT_TYPE,
        }

        self.assertTupleEqual(
            MailjetEmailProvider.parse_event_webhook(event_info),
            (str(event_info["MessageID"]), parsed_event_info),
        )

    def test_parse_event_webhook_for_email_hard_bounced_event(self):
        event_info = {
            "event": "bounce",
            "time": 1430812195,
            "MessageID": 13792286917004336,
            "Message_GUID": "1ab23cd4-e567-8901-2345-6789f0gh1i2j",
            "email": "bounce@mailjet.com",
            "mj_campaign_id": 0,
            "mj_contact_id": 0,
            "customcampaign": "",
            "CustomID": "helloworld",
            "Payload": "",
            "blocked": False,
            "hard_bounce": True,
            "error_related_to": "recipient",
            "error": "user unknown",
        }

        parsed_event_info = {
            "event_at": pytz.UTC.localize(
                datetime.utcfromtimestamp(event_info["time"])
            ),
            "event_info": event_info,
            "event_type": EventLog.EMAIL_HARD_BOUNCED_EVENT_TYPE,
        }

        self.assertTupleEqual(
            MailjetEmailProvider.parse_event_webhook(event_info),
            (str(event_info["MessageID"]), parsed_event_info),
        )

    def test_parse_event_webhook_for_email_soft_bounced_event(self):
        event_info = {
            "event": "bounce",
            "time": 1430812195,
            "MessageID": 13792286917004336,
            "Message_GUID": "1ab23cd4-e567-8901-2345-6789f0gh1i2j",
            "email": "bounce@mailjet.com",
            "mj_campaign_id": 0,
            "mj_contact_id": 0,
            "customcampaign": "",
            "CustomID": "helloworld",
            "Payload": "",
            "blocked": False,
            "error_related_to": "recipient",
            "error": "user unknown",
        }

        parsed_event_info = {
            "event_at": pytz.UTC.localize(
                datetime.utcfromtimestamp(event_info["time"])
            ),
            "event_info": event_info,
            "event_type": EventLog.EMAIL_SOFT_BOUNCED_EVENT_TYPE,
        }

        self.assertTupleEqual(
            MailjetEmailProvider.parse_event_webhook(event_info),
            (str(event_info["MessageID"]), parsed_event_info),
        )

    def test_parse_event_webhook_for_spam_event(self):
        event_info = {
            "event": "spam",
            "time": 1430812195,
            "MessageID": 13792286917004336,
            "Message_GUID": "1ab23cd4-e567-8901-2345-6789f0gh1i2j",
            "email": "bounce@mailjet.com",
            "mj_campaign_id": 0,
            "mj_contact_id": 0,
            "customcampaign": "",
            "CustomID": "helloworld",
            "Payload": "",
            "source": "JMRPP",
        }
        parsed_event_info = {
            "event_at": pytz.UTC.localize(
                datetime.utcfromtimestamp(event_info["time"])
            ),
            "event_info": event_info,
            "event_type": EventLog.EMAIL_SPAMMED_EVENT_TYPE,
        }

        self.assertTupleEqual(
            MailjetEmailProvider.parse_event_webhook(event_info),
            (str(event_info["MessageID"]), parsed_event_info),
        )

    def test_parse_event_webhook_for_not_defined_email_event(self):
        event_info = {
            "event": "not_defined",
            "time": 1433103519,
            "MessageID": 19421777396190490,
            "Message_GUID": "1ab23cd4-e567-8901-2345-6789f0gh1i2j",
            "email": "api@mailjet.com",
            "mj_campaign_id": 7173,
            "mj_contact_id": 320,
            "customcampaign": "",
            "CustomID": "helloworld",
            "Payload": "",
            "ip": "127.0.0.1",
            "geo": "US",
            "agent": "Mozilla/5.0 (Windows NT 5.1; rv:11.0) Gecko Firefox/11.0",
        }

        with self.assertRaises(KeyError):
            MailjetEmailProvider.parse_event_webhook(event_info)

    def test_send_email(self):
        data = {"Email": "test@example.com"}

        with mock.patch.object(
            MailjetEmailProvider, "_create_email_data"
        ) as mocked_create_email_data, mock.patch(
            "django_email.providers.mailjet.MailjetEmailProvider.sdk_client"
        ) as mailjet_sdk_client:
            mocked_create_email_data.return_value = data
            sdk_send_method = mailjet_sdk_client.send.create

            MailjetEmailProvider.send_email(self.email_log)

            mocked_create_email_data.assert_called_with(self.email_log)
            sdk_send_method.assert_called_with(data=data)

    def test_handle_send_email_response(self):
        response_from_provider = [{"To": {"Message_Id": "1234"}}]
        parsed_response = [{"message_id": "1234"}]
        recipient_response = {"message_id": "1234", "email_log": self.email_log}

        with mock.patch.object(
            MailjetEmailProvider, "parse_send_email_response_for_email_log"
        ) as mocked_parse_send_email_response, mock.patch.object(
            EmailActivityTracker, "track_recipient"
        ) as mocked_track_recipient, mock.patch.object(
            EmailLog, "update_fields"
        ) as mocked_email_log_update_fields:
            mocked_parse_send_email_response.return_value = (
                EmailLog.EMAIL_STATUS_SENT,
                parsed_response,
            )

            MailjetEmailProvider.handle_send_email_response(
                response_from_provider, self.email_log
            )

            mocked_parse_send_email_response.assert_called_with(response_from_provider)
            mocked_email_log_update_fields.assert_called_with(
                dispatch_status=EmailLog.EMAIL_STATUS_SENT
            )
            mocked_track_recipient.assert_has_calls([mock.call(recipient_response)])

            # Below is the test for the scenario when error is received as the response
            mocked_parse_send_email_response.return_value = (
                EmailLog.EMAIL_STATUS_FAILED,
                parsed_response,
            )

            MailjetEmailProvider.handle_send_email_response(
                response_from_provider, self.email_log
            )

            mocked_parse_send_email_response.assert_called_with(response_from_provider)
            mocked_email_log_update_fields.assert_called_with(
                dispatch_status=EmailLog.EMAIL_STATUS_FAILED, error_info=parsed_response
            )

            mocked_parse_send_email_response.return_value = (
                "Undefined Status",
                parsed_response,
            )

            MailjetEmailProvider.handle_send_email_response(
                response_from_provider, self.email_log
            )
            # Call count of update fields would remain 2 as email log fields would not be updated for undefined
            # email status
            self.assertEqual(mocked_email_log_update_fields.call_count, 2)

    def test_handle_event_webhook(self):
        event_info = {"event": "sent", "MessageId": "12345"}
        parsed_event_data = {"event": EventLog.EMAIL_DELIVERED_EVENT_TYPE}
        event_data_for_model = {
            **parsed_event_data,
            "email_activity_tracker": self.email_activity_tracker,
        }

        with mock.patch.object(
            MailjetEmailProvider, "parse_event_webhook"
        ) as mocked_abstract_parse_event_webhook, mock.patch.object(
            EmailActivityTracker, "get_by_message_id"
        ) as mocked_get_by_message_id, mock.patch.object(
            EventLog, "add_new_event_log"
        ) as mocked_add_event_log, mock.patch.object(
            EmailActivityTracker, "update_fields_on_event"
        ) as mocked_email_activity_tracker_update_fields:

            mocked_abstract_parse_event_webhook.return_value = (
                event_info["MessageId"],
                parsed_event_data,
            )
            mocked_get_by_message_id.return_value = self.email_activity_tracker
            mocked_add_event_log.return_value = self.event_log

            MailjetEmailProvider.handle_event_webhook(event_info)

            mocked_abstract_parse_event_webhook.assert_called_with(event_info)
            mocked_get_by_message_id.assert_called_with(event_info["MessageId"])
            self.assertEqual(event_data_for_model, parsed_event_data)
            mocked_email_activity_tracker_update_fields.assert_called_with(
                self.event_log.event_type
            )

            # Below is the test for the scenario when no activity tracker is found in db and an
            # exception should be raised in that case
            with self.assertRaises(EmailActivityTrackerNotFoundException):
                mocked_abstract_parse_event_webhook.return_value = (
                    event_info["MessageId"],
                    parsed_event_data,
                )
                mocked_get_by_message_id.return_value = None
                mocked_add_event_log.return_value = self.event_log

                MailjetEmailProvider.handle_event_webhook(event_info)
