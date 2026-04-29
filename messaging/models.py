# File: messaging/models.py - Noah Gil De Matos Jimenez (with Aditya integration)
"""Internal messaging - draft / send / inbox flow."""

from django.conf import settings
from django.db import models


class Message(models.Model):
    DRAFT = "DRAFT"
    SENT = "SENT"
    STATUS_CHOICES = [(DRAFT, "Draft"), (SENT, "Sent")]

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages_sent",
    )
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.status})"

    @property
    def is_sent(self):
        return self.status == self.SENT


class MessageRecipient(models.Model):
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="recipients"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages_received",
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("message", "recipient")

    def __str__(self):
        return f"{self.message} -> {self.recipient}"
