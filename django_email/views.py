from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from .tasks import handle_webhook


class EmailEventWebhookView(APIView):
    authentication_classes = ()
    permission_classes = ()

    # Not using serializer here as the fields are dynamic in the json provided by webhook.
    def post(self, request, email_provider):
        # Using request.body instead of request.data here because keys in the dict are not
        # preserved in original format in request.data
        handle_webhook.apply_async((request.body.decode('utf-8'), email_provider))

        return HttpResponse(status=status.HTTP_200_OK)
