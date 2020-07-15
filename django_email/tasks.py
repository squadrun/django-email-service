import json

from celery import shared_task

from .exceptions import EmailActivityTrackerNotFoundException
from .services import EmailService


@shared_task(
    autoretry_for=(EmailActivityTrackerNotFoundException,), default_retry_delay=60,
    retry_kwargs={'max_retries': 5}
)
def handle_webhook(request_body: str, email_provider):
    event_info = json.loads(request_body)
    EmailService.handle_event_webhook(email_provider, event_info)
