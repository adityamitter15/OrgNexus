# File: organisation/tests.py - Noah Gil De Matos Jimenez

import datetime as dt
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Department, DepartmentHead, FocusArea


def _login(client):
    u = User.objects.create_user(
        "noah", email="noah@sky.example", password="GoodPassword!1"
    )
    u.email_verified = True
    u.save()
    client.force_login(u)
    return u


class DepartmentModelTests(TestCase):
    def test_slug_auto_generated(self):
        """UC08-01. Pre: none. Steps: create Department without slug.
        Expected: slug derived from name. Priority: LOW."""
        d = Department.objects.create(name="xTV_Web")
        self.assertEqual(d.slug, "xtv_web")

    def test_only_one_active_department_head_at_a_time(self):
        """UC08-02. Pre: dept with active head. Steps: try to create a
        second active head for the same dept. Expected: IntegrityError.
        Priority: HIGH."""
        d = Department.objects.create(name="xTV_Web")
        u1 = User.objects.create_user("h1", email="h1@sky.example", password="x" * 12)
        u2 = User.objects.create_user("h2", email="h2@sky.example", password="x" * 12)
        DepartmentHead.objects.create(user=u1, department=d, appointed=dt.date.today())
        with self.assertRaises(IntegrityError):
            DepartmentHead.objects.create(
                user=u2, department=d, appointed=dt.date.today()
            )


class FocusAreaTests(TestCase):
    def test_focus_area_unique_name(self):
        """UC09-01. Pre: 'Streaming' focus area exists. Steps: try to
        create another with the same name. Expected: IntegrityError.
        Priority: LOW."""
        FocusArea.objects.create(name="Streaming")
        with self.assertRaises(IntegrityError):
            FocusArea.objects.create(name="Streaming")


class OrgStructureViewTests(TestCase):
    def test_org_structure_lists_every_department(self):
        """UC10-01. Pre: two departments seeded. Steps: GET
        /organisation/structure/. Expected: 200 with both names.
        Priority: MEDIUM."""
        _login(self.client)
        Department.objects.create(name="Alpha")
        Department.objects.create(name="Beta")
        response = self.client.get(reverse("organisation:structure"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha")
        self.assertContains(response, "Beta")
