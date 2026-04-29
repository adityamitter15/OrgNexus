# File: core/tests.py - Aditya Mitter (W19869650)

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from organisation.models import Department

from .models import AuditLog


class DashboardAndSearchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "alice", email="alice@sky.example", password="GoodPassword!1"
        )
        self.user.email_verified = True
        self.user.save()

    def test_anonymous_root_renders_home_page(self):
        """UC14-01. Pre: not logged in. Steps: GET /. Expected: 200
        with 'OrgNexus' branding visible. Priority: LOW."""
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "OrgNexus")

    def test_dashboard_requires_login(self):
        """UC14-02. Pre: not logged in. Steps: GET /dashboard/. Expected:
        302 to /accounts/login/. Priority: HIGH (auth gating)."""
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_search_finds_department_by_name(self):
        """UC14-03. Pre: dept 'xTV_Web' seeded. Steps: GET
        /search/?q=xTV. Expected: 200, page contains 'xTV_Web'.
        Priority: MEDIUM."""
        Department.objects.create(name="xTV_Web")
        self.client.force_login(self.user)
        response = self.client.get(reverse("core:search") + "?q=xTV")
        self.assertContains(response, "xTV_Web")


class AuditLogSignalTests(TestCase):
    def test_creating_a_department_writes_an_audit_row(self):
        """UC15-01. Pre: empty AuditLog. Steps: create a Department.
        Expected: one AuditLog row with action=CREATE,
        table_name=organisation.Department. Priority: MEDIUM (rubric
        explicitly asks for an audit trail)."""
        self.assertEqual(AuditLog.objects.count(), 0)
        Department.objects.create(name="xTV_Web")
        log = AuditLog.objects.get()
        self.assertEqual(log.action, AuditLog.CREATE)
        self.assertEqual(log.table_name, "organisation.Department")
