# File: reports/tests.py - Aditya Mitter (W19869650)

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from organisation.models import Department
from teams.models import Team


def _login(client):
    u = User.objects.create_user(
        "rita", email="rita@sky.example", password="GoodPassword!1"
    )
    u.email_verified = True
    u.save()
    client.force_login(u)
    return u


class ReportsExportTests(TestCase):
    def test_pdf_endpoint_returns_pdf_bytes(self):
        """UC13-01. Pre: department + team seeded. Steps: GET
        /reports/pdf/. Expected: 200, Content-Type=application/pdf,
        body starts with %PDF. Priority: MEDIUM."""
        _login(self.client)
        Department.objects.create(name="xTV_Web")
        response = self.client.get(reverse("reports:pdf"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_xlsx_endpoint_has_three_sheets(self):
        """UC13-02. Pre: minimal data seeded. Steps: GET /reports/xlsx/.
        Expected: workbook with sheets Departments / Teams / Projects.
        Priority: MEDIUM."""
        _login(self.client)
        Department.objects.create(name="xTV_Web")
        response = self.client.get(reverse("reports:xlsx"))
        self.assertEqual(response.status_code, 200)
        # openpyxl.load_workbook can read from BytesIO.
        from io import BytesIO
        from openpyxl import load_workbook
        wb = load_workbook(BytesIO(response.content))
        self.assertEqual(
            sorted(wb.sheetnames),
            sorted(["Departments", "Teams", "Projects"]),
        )

    def test_orphan_teams_view_lists_only_unassigned(self):
        """UC13-03. Pre: two teams, one with manager. Steps: GET
        /reports/teams-without-managers/. Expected: only the orphan
        listed. Priority: LOW."""
        rita = _login(self.client)
        d = Department.objects.create(name="xTV_Web")
        Team.objects.create(name="Code Warriors", department=d, manager=rita)
        Team.objects.create(name="The Debuggers", department=d)
        response = self.client.get(reverse("reports:orphans"))
        self.assertContains(response, "The Debuggers")
        self.assertNotContains(response, "Code Warriors")
