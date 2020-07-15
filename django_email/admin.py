from django.contrib import admin
from nested_admin.nested import NestedTabularInline, NestedModelAdmin

from .models import EmailLog, EmailActivityTracker, EventLog


class NonEditableAdminMixin(object):
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return obj is None

    def has_delete_permission(self, request, obj=None):
        return False


class EventLogAdmin(NonEditableAdminMixin, NestedTabularInline):
    model = EventLog
    ordering = ("-event_at",)


class EmailActivityTrackerAdmin(NonEditableAdminMixin, NestedTabularInline):
    model = EmailActivityTracker
    inlines = [EventLogAdmin]


class EmailLogAdmin(NonEditableAdminMixin, NestedModelAdmin):
    inlines = [EmailActivityTrackerAdmin]
    list_display = (
        "id",
        "email_provider",
        "from_email",
        "to_emails",
        "subject",
        "template_id",
        "dispatch_status",
        "created_at",
    )
    list_filter = (
        "created_at",
        "dispatch_status",
        "email_provider",
        "from_email",
        "template_id",
        "subject",
    )
    search_fields = ("to_emails", "cc_emails", "bcc_emails")


admin.site.register(EmailLog, EmailLogAdmin)
