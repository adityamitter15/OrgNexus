# File: core/signals.py - Aditya Mitter (W19869650)
"""Single signal handler that turns ORM saves and deletes into AuditLog rows.

Only the tables that match the brief's 'audit trail of edits' phrasing
are watched - we don't want to spam the log with every Session row.

Hook from `core/apps.py.ready()`.
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict

from .models import AuditLog


_WATCHED = (
    "organisation.Department",
    "organisation.FocusArea",
    "organisation.DepartmentHead",
    "teams.Team",
    "teams.TeamDependency",
    "teams.Staff",
    "teams.TeamLeader",
    "reports.Project",
)


def _is_watched(sender):
    label = f"{sender._meta.app_label}.{sender.__name__}"
    return label in _WATCHED


def _serialise(instance):
    """Cheap dict snapshot - skips relations to avoid recursion."""
    try:
        return {
            k: (v if isinstance(v, (str, int, float, bool, type(None))) else str(v))
            for k, v in model_to_dict(instance).items()
        }
    except Exception:
        return {"repr": str(instance)}


@receiver(post_save)
def audit_save(sender, instance, created, **kwargs):
    if not _is_watched(sender):
        return
    AuditLog.objects.create(
        action=AuditLog.CREATE if created else AuditLog.UPDATE,
        table_name=sender._meta.label,
        row_id=str(getattr(instance, "pk", "")),
        before={},
        after=_serialise(instance),
    )


@receiver(post_delete)
def audit_delete(sender, instance, **kwargs):
    if not _is_watched(sender):
        return
    AuditLog.objects.create(
        action=AuditLog.DELETE,
        table_name=sender._meta.label,
        row_id=str(getattr(instance, "pk", "")),
        before=_serialise(instance),
        after={},
    )
