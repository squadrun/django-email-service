from django.urls import path

from .views import EmailEventWebhookView

urlpatterns = [
    path(
        "<str:email_provider>/event/",
        EmailEventWebhookView.as_view(),
        name="email_event_webhook",
    ),
]
