# File: core/admin.py - Aditya Mitter (W19869650)

from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "action", "table_name", "row_id", "actor")
    list_filter = ("action", "table_name")
    search_fields = ("table_name", "row_id", "actor__username")
    readonly_fields = (
        "actor",
        "action",
        "table_name",
        "row_id",
        "before",
        "after",
        "timestamp",
    )

    def has_add_permission(self, request):
        # Audit logs are written by the app, never by hand.
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Allow superuser cleanup, but warn the report we did so.
        return request.user.is_superuser
