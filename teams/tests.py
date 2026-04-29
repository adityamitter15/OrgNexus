# File: teams/tests.py - Aditya Mitter (W19869650)
"""Tests for the Team menu - my (Aditya's) individual element."""

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from organisation.models import Department

from .models import Team, TeamDependency


def _logged_in_user(client, username="aditya"):
    user = User.objects.create_user(
        username, email=f"{username}@sky.example", password="GoodPassword!1"
    )
    user.email_verified = True
    user.save()
    client.force_login(user)
    return user


class TeamModelTests(TestCase):
    def test_slug_is_auto_generated_from_name(self):
        """UC04-01. Pre: Department exists. Steps: create Team without
        slug. Expected: slug is the slugified name. Priority: LOW."""
        d = Department.objects.create(name="xTV_Web")
        t = Team.objects.create(name="Code Warriors", department=d)
        self.assertEqual(t.slug, "code-warriors")

    def test_slug_is_unique_even_when_names_repeat(self):
        """UC04-02. Pre: 'Code Warriors' team exists in dept A. Steps:
        create another 'Code Warriors' in dept B. Expected: second slug
        ends with '-2'. Priority: LOW."""
        d1 = Department.objects.create(name="Alpha")
        d2 = Department.objects.create(name="Beta")
        Team.objects.create(name="Code Warriors", department=d1)
        t2 = Team.objects.create(name="Code Warriors", department=d2)
        self.assertEqual(t2.slug, "code-warriors-2")

    def test_unique_together_blocks_duplicate_team_in_same_dept(self):
        """UC04-03. Pre: team A in dept X. Steps: create team A in dept
        X again. Expected: IntegrityError. Priority: HIGH."""
        d = Department.objects.create(name="xTV_Web")
        Team.objects.create(name="Code Warriors", department=d)
        with self.assertRaises(IntegrityError):
            Team.objects.create(name="Code Warriors", department=d)


class TeamSearchTests(TestCase):
    def setUp(self):
        self.user = _logged_in_user(self.client)
        self.dept = Department.objects.create(name="xTV_Web")
        Team.objects.create(name="Code Warriors", department=self.dept)
        Team.objects.create(name="The Debuggers", department=self.dept)

    def test_search_by_team_name_returns_only_match(self):
        """UC05-01. Pre: logged in, two teams seeded. Steps: GET
        /teams/?q=Warriors. Expected: 200, only Code Warriors row.
        Post: no DB change. Priority: HIGH."""
        response = self.client.get(reverse("teams:list") + "?q=Warriors")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Code Warriors")
        self.assertNotContains(response, "The Debuggers")

    def test_anonymous_user_redirected_to_login(self):
        """UC05-02. Pre: not logged in. Steps: GET /teams/. Expected:
        302 to /accounts/login/. Priority: HIGH (auth gating)."""
        self.client.logout()
        response = self.client.get(reverse("teams:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])


class TeamDetailTests(TestCase):
    def test_detail_page_shows_dependencies_and_members(self):
        """UC06-01. Pre: a team with one upstream dep + one staff member.
        Steps: GET /teams/<slug>/. Expected: page lists upstream team
        and member name. Priority: HIGH."""
        user = _logged_in_user(self.client)
        d = Department.objects.create(name="xTV_Web")
        upstream = Team.objects.create(name="Bit Masters", department=d)
        downstream = Team.objects.create(name="Code Warriors", department=d)
        TeamDependency.objects.create(upstream=upstream, downstream=downstream)
        from .models import Staff
        Staff.objects.create(user=user, team=downstream, role="Engineer")

        response = self.client.get(reverse("teams:detail", args=[downstream.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bit Masters")
        self.assertContains(response, "Engineer")


class DependencyConstraintTests(TestCase):
    def test_self_dependency_is_rejected_by_db(self):
        """UC07-01. Pre: a team exists. Steps: create dependency with
        upstream==downstream. Expected: IntegrityError from CHECK
        constraint. Priority: HIGH (data integrity)."""
        d = Department.objects.create(name="xTV_Web")
        t = Team.objects.create(name="Code Warriors", department=d)
        with self.assertRaises(IntegrityError):
            TeamDependency.objects.create(upstream=t, downstream=t)
