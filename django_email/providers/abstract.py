from ..exceptions import EmailActivityTrackerNotFoundException
from ..models import EmailActivityTracker, EmailLog, EventLog


class AbstractEmailProvider(object):
    provider = None

    @classmethod
    def send_email(cls, email_log: EmailLog):
        raise NotImplementedError

    @classmethod
    def parse_send_email_response_for_email_log(cls, response):
        raise NotImplementedError

    @classmethod
    def parse_event_webhook(cls, event_info):
        raise NotImplementedError

    @classmethod
    def handle_send_email_response(cls, response, email_log):
        email_status, parsed_response = cls.parse_send_email_response_for_email_log(
            response
        )
        if email_status == EmailLog.EMAIL_STATUS_SENT:
            email_log.update_fields(dispatch_status=email_status)

            for recipient_data in parsed_response:
                recipient_data["email_log"] = email_log
                EmailActivityTracker.track_recipient(recipient_data)

        elif email_status == EmailLog.EMAIL_STATUS_FAILED:
            email_log.update_fields(
                dispatch_status=email_status, error_info=parsed_response
            )

    # Handle this via creating a Celery task that retries at most 5 times
    # Figure out how to reference celery @app.task inside a package

    @classmethod
    def handle_event_webhook(cls, event_info):
        message_id, parsed_event_data = cls.parse_event_webhook(event_info)

        email_activity_tracker = EmailActivityTracker.get_by_message_id(message_id)
        if email_activity_tracker is None:
            # raise a normal exception here
            raise EmailActivityTrackerNotFoundException()

        parsed_event_data["email_activity_tracker"] = email_activity_tracker
        event_log = EventLog.add_new_event_log(parsed_event_data)

        email_activity_tracker.update_fields_on_event(event_log.event_type)
