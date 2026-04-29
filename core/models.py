# File: core/models.py - Aditya Mitter (W19869650)
"""Cross-cutting models that don't belong to one app.

AuditLog is the explicit 'audit trail of edits and updates' the brief
requires. We keep before/after JSON snapshots so the admin can see
exactly what changed.
"""

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ACTION_CHOICES = [
        (CREATE, "Create"),
        (UPDATE, "Update"),
        (DELETE, "Delete"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_actions",
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    table_name = models.CharField(max_length=80)
    row_id = models.CharField(max_length=80)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["table_name", "row_id"]),
            models.Index(fields=["-timestamp"]),
        ]

    def __str__(self):
        return f"{self.action} {self.table_name}#{self.row_id} @ {self.timestamp:%Y-%m-%d}"
