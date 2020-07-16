====================
Django Email Service
====================

Django Email Service is a Django app that allows you to send emails using mailjet (for now) in a convenient way.

Quick start
-----------

1. Add "django_email" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'django_email',
    ]

2. Set the following variables in your settings file::

    MAILJET_API_KEY = 'mailjet-api-key'
    MAILJET_SECRET_KEY = 'mailjet-secret-key'
    DEFAULT_FROM_EMAIL = 'default-from-email'
    DEFAULT_FROM_NAME = 'default-from-name'

3. Include the django_email URLconf in your project urls.py like this::

    path('email/', include('django_email.urls')),

4. Run ``python manage.py migrate`` to create the django_email models.

5. Start the development server and visit http://127.0.0.1:8000/admin/
   to view email log (you'll need the Admin app enabled).

6. Visit http://127.0.0.1:8000/django_email/ to see the email logs along with its events.


Usage
------

.. code-block:: python

    from django_email.services import EmailService
    from django_email.constants import EMAIL_PROVIDER_MAILJET

    EmailService.send_email(
        to_emails=['foo@example.com', 'bar@example.com'],
        subject='A test Email',
        cc_emails=['baz@example.com'],
        bcc_emails=['tom@example.com'],
        body="<html><h1>This is a test email</h1></html>",
        template_id=None,
        template_dynamic_data=None,
        from_email=settings.DEFAULT_FROM_EMAIL,
        from_name=settings.DEFAULT_FROM_NAME,
        email_provider=EMAIL_PROVIDER_MAILJET,
        reply_to='admin@example.com'
    )


Notes
------

1. By default the celery messages go into the default celery queue which is named as ``celery``. You can change this
   be routing messages from default queue to some other queue.
   https://stackoverflow.com/questions/10707287/django-celery-routing-problems

2. You need to configure a message broker in your application like RabbitMQ or Redis where messages are stored and
   consumed by celery workers.

