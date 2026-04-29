# File: scheduler/models.py - Aditya Mitter (W19869650)
"""Meeting scheduler - matches the brief's 'Schedule' menu items.

A Meeting has a single creator and a M2M of participants via the
MeetingParticipant junction (so we can track invite responses).
"""

from django.conf import settings
from django.db import models


class Meeting(models.Model):
    NONE = "NONE"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    RECURRENCE_CHOICES = [
        (NONE, "One-off"),
        (WEEKLY, "Weekly"),
        (MONTHLY, "Monthly"),
    ]

    title = models.CharField(max_length=200)
    date_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    platform = models.CharField(max_length=80, blank=True)  # Zoom / Teams / Meet
    location_url = models.URLField(blank=True)
    agenda = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meetings_created",
    )
    recurrence = models.CharField(
        max_length=10, choices=RECURRENCE_CHOICES, default=NONE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date_time"]

    def __str__(self):
        return f"{self.title} @ {self.date_time:%Y-%m-%d %H:%M}"


class MeetingParticipant(models.Model):
    INVITED = "INVITED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    STATUS_CHOICES = [
        (INVITED, "Invited"),
        (ACCEPTED, "Accepted"),
        (DECLINED, "Declined"),
    ]

    meeting = models.ForeignKey(
        Meeting, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meeting_invites",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=INVITED)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("meeting", "user")

    def __str__(self):
        return f"{self.user} -> {self.meeting} ({self.status})"
