import logging

from django.conf import settings

from .constants import DEFAULT_EMAIL_PROVIDER
from .models import EmailLog
from .providers.abstract import AbstractEmailProvider

logger = logging.getLogger(__name__)


class EmailService(object):
    @classmethod
    def _get_provider_class_for_provider(cls, provider: str):
        for provider_class in AbstractEmailProvider.__subclasses__():
            if provider_class.provider == provider:
                return provider_class

        else:
            logger.warning(
                f"Unsupported email provider {provider} requested for service"
            )
            raise ValueError(
                f"Provider {provider} is not supported by the email module as of today."
            )

    @classmethod
    def send_email(
        cls,
        to_emails: list,
        subject,
        cc_emails: list = None,
        bcc_emails: list = None,
        body=None,
        template_id=None,
        template_dynamic_data: dict = None,
        from_email=settings.DEFAULT_FROM_EMAIL,
        from_name=settings.DEFAULT_FROM_NAME,
        email_provider=DEFAULT_EMAIL_PROVIDER,
        reply_to=None
    ):
        provider_class = cls._get_provider_class_for_provider(email_provider)

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
            reply_to
        )

        response = provider_class.send_email(email_log)
        provider_class.handle_send_email_response(response, email_log)

    @classmethod
    def handle_event_webhook(cls, email_provider, event_info):
        provider_class = cls._get_provider_class_for_provider(email_provider)

        provider_class.handle_event_webhook(event_info)
