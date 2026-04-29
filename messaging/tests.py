# File: messaging/tests.py - Noah Gil De Matos Jimenez

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import Message, MessageRecipient


class MessageFlowTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            "alice", email="alice@sky.example", password="GoodPassword!1"
        )
        self.alice.email_verified = True
        self.alice.save()
        self.bob = User.objects.create_user(
            "bob", email="bob@sky.example", password="GoodPassword!1"
        )
        self.bob.email_verified = True
        self.bob.save()
        self.client.force_login(self.alice)

    def test_create_message_as_sent_creates_recipient_rows(self):
        """UC11-01. Pre: alice + bob exist. Steps: POST /messages/new/
        with action=send. Expected: 302, Message status=SENT, one
        MessageRecipient row for bob. Priority: HIGH."""
        response = self.client.post(
            reverse("messaging:create"),
            {
                "recipients": [self.bob.id],
                "subject": "Hey",
                "body": "Quick note about the team registry.",
                "action": "send",
            },
        )
        self.assertEqual(response.status_code, 302)
        msg = Message.objects.get(subject="Hey")
        self.assertEqual(msg.status, Message.SENT)
        self.assertEqual(msg.recipients.count(), 1)
        self.assertEqual(msg.recipients.first().recipient, self.bob)

    def test_save_as_draft_does_not_set_sent_at(self):
        """UC11-02. Pre: as above. Steps: POST with action=draft.
        Expected: status=DRAFT, sent_at is null. Priority: MEDIUM."""
        response = self.client.post(
            reverse("messaging:create"),
            {
                "recipients": [self.bob.id],
                "subject": "Draft",
                "body": "Not yet ready.",
                "action": "draft",
            },
        )
        self.assertEqual(response.status_code, 302)
        msg = Message.objects.get(subject="Draft")
        self.assertEqual(msg.status, Message.DRAFT)
        self.assertIsNone(msg.sent_at)

    def test_inbox_marks_message_as_read_on_open(self):
        """UC11-03. Pre: bob received an unread message. Steps: bob
        visits /messages/<id>/. Expected: MessageRecipient.is_read
        becomes True. Priority: MEDIUM."""
        msg = Message.objects.create(
            sender=self.alice,
            subject="Hi bob",
            body="Test.",
            status=Message.SENT,
            sent_at=timezone.now(),
        )
        rcpt = MessageRecipient.objects.create(message=msg, recipient=self.bob)

        self.client.force_login(self.bob)
        response = self.client.get(reverse("messaging:detail", args=[msg.pk]))
        self.assertEqual(response.status_code, 200)
        rcpt.refresh_from_db()
        self.assertTrue(rcpt.is_read)
