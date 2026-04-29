# File: scheduler/tests.py - Aditya Mitter (W19869650)

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import Meeting, MeetingParticipant


class MeetingFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "alice", email="alice@sky.example", password="GoodPassword!1"
        )
        self.user.email_verified = True
        self.user.save()
        self.client.force_login(self.user)

    def test_meeting_create_invites_creator_as_accepted(self):
        """UC12-01. Pre: alice logged in. Steps: POST /schedule/new/
        with future date. Expected: meeting saved, creator listed as
        ACCEPTED participant. Priority: MEDIUM."""
        when = timezone.now() + timezone.timedelta(days=2)
        response = self.client.post(
            reverse("scheduler:create"),
            {
                "title": "Standup",
                "date_time": when.strftime("%Y-%m-%dT%H:%M"),
                "duration_minutes": 30,
                "platform": "Zoom",
                "location_url": "",
                "agenda": "Daily sync",
                "recurrence": Meeting.NONE,
                "invitees": [],
            },
        )
        self.assertEqual(response.status_code, 302)
        meeting = Meeting.objects.get(title="Standup")
        invite = MeetingParticipant.objects.get(meeting=meeting, user=self.user)
        self.assertEqual(invite.status, MeetingParticipant.ACCEPTED)

    def test_respond_endpoint_marks_decline(self):
        """UC12-02. Pre: alice invited to a meeting. Steps: GET
        /schedule/<id>/respond/declined/. Expected: invite status
        becomes DECLINED. Priority: LOW."""
        m = Meeting.objects.create(
            title="Sprint review",
            date_time=timezone.now() + timezone.timedelta(days=3),
            created_by=self.user,
        )
        invite = MeetingParticipant.objects.create(meeting=m, user=self.user)
        self.client.get(reverse("scheduler:respond", args=[m.pk, "declined"]))
        invite.refresh_from_db()
        self.assertEqual(invite.status, MeetingParticipant.DECLINED)
