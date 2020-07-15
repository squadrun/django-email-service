import logging
from datetime import datetime

import pytz
from django.conf import settings
from mailjet_rest import Client

from ..constants import EMAIL_PROVIDER_MAILJET
from ..models import EventLog, EmailActivityTracker, EmailLog
from ..providers.abstract import AbstractEmailProvider

logger = logging.getLogger(__name__)


class MailjetEmailProvider(AbstractEmailProvider):

    provider = EMAIL_PROVIDER_MAILJET
    sdk_client = Client(
        auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY),
        version="v3.1",
    )

    @classmethod
    def _create_email_data(cls, email_log):
        message = {
            "From": {"Email": email_log.from_email, "Name": email_log.from_name or email_log.from_email},
            "Subject": email_log.subject,
            "To": [{"Email": to_email} for to_email in email_log.to_emails],
        }

        if email_log.body:
            message["HTMLPart"] = email_log.body

        if email_log.cc_emails:
            message["Cc"] = [{"Email": cc_email} for cc_email in email_log.cc_emails]

        if email_log.bcc_emails:
            message["Bcc"] = [
                {"Email": bcc_email} for bcc_email in email_log.bcc_emails
            ]

        if email_log.template_id:
            message["TemplateID"] = email_log.template_id
            message["TemplateLanguage"] = True
            message["Variables"] = email_log.template_dynamic_data

        if email_log.extra:
            message.update(email_log.extra or {})

        return {"Messages": [message]}

    @classmethod
    def send_email(cls, email_log):
        data = cls._create_email_data(email_log)
        response = cls.sdk_client.send.create(data=data)

        return response

    @classmethod
    def parse_send_email_response_for_email_log(cls, response):
        response_data = response.json()

        if response.ok:
            recipients_response_data = response_data["Messages"][0]

            recipient_vs_type = {
                "To": EmailActivityTracker.TO_RECIPIENT_TYPE,
                "Cc": EmailActivityTracker.CC_RECIPIENT_TYPE,
                "Bcc": EmailActivityTracker.BCC_RECIPIENT_TYPE,
            }

            parsed_response = []
            for recipient in recipient_vs_type.keys():
                parsed_response += [
                    {
                        "recipient_type": recipient_vs_type[recipient],
                        "email_address": recipient_response_data["Email"],
                        "message_id": str(recipient_response_data["MessageID"]),
                    }
                    for recipient_response_data in recipients_response_data[recipient]
                ]

            return EmailLog.EMAIL_STATUS_SENT, parsed_response

        else:
            error_info = {"error": response_data}

            logger.exception(
                "Mailjet: Could not send email",
                extra={"status code": response.status_code, "errors": error_info},
            )

            return EmailLog.EMAIL_STATUS_FAILED, error_info

    @classmethod
    def parse_event_webhook(cls, event_info):
        message_id = str(event_info["MessageID"])

        event_vs_event_type = {
            "open": EventLog.EMAIL_OPENED_EVENT_TYPE,
            "click": EventLog.EMAIL_CLICKED_EVENT_TYPE,
            "spam": EventLog.EMAIL_SPAMMED_EVENT_TYPE,
            "sent": EventLog.EMAIL_DELIVERED_EVENT_TYPE,
            "bounce": EventLog.EMAIL_HARD_BOUNCED_EVENT_TYPE
            if event_info.get("hard_bounce")
            else EventLog.EMAIL_SOFT_BOUNCED_EVENT_TYPE,
        }

        event_data = {
            "event_at": pytz.UTC.localize(
                datetime.utcfromtimestamp(event_info["time"])
            ),
            "event_info": event_info,
            "event_type": event_vs_event_type[event_info["event"]],
        }

        return message_id, event_data
