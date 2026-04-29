# File: accounts/tests.py - Aditya Mitter (W19869650)
"""Test plan rows for the auth flow.

Each test method's docstring is the row we transcribe into the report's
test-plan table - UC ID, pre-condition, steps, expected result, post-
condition, priority.
"""

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import User


class RegistrationFlowTests(TestCase):
    """UC01 - Self-register and verify email."""

    def test_register_creates_inactive_user_and_sends_email(self):
        """UC01-01.
        Pre: no account with this email.
        Steps: POST /accounts/register/ with valid payload.
        Expected: 302 redirect, user row exists with is_active=False
            and email_verified=False, one verification email queued.
        Post: User exists in DB but cannot log in.
        Priority: HIGH.
        """
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "alice",
                "email": "alice@sky.example",
                "full_name": "Alice Tester",
                "job_title": "Engineer",
                "password1": "S0lidPassw0rd!",
                "password2": "S0lidPassw0rd!",
            },
        )
        self.assertEqual(response.status_code, 302)
        u = User.objects.get(username="alice")
        self.assertFalse(u.is_active)
        self.assertFalse(u.email_verified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Confirm your OrgNexus account", mail.outbox[0].subject)

    def test_verify_link_activates_account(self):
        """UC01-02.
        Pre: registered but unverified user.
        Steps: GET /accounts/verify/<uid>/<token>/ with valid token.
        Expected: 302 to login page, is_active and email_verified now True.
        Post: User can log in.
        Priority: HIGH.
        """
        u = User.objects.create_user(
            "bob", email="bob@sky.example", password="S0lidPassw0rd!"
        )
        u.is_active = False
        u.email_verified = False
        u.save()
        uid = urlsafe_base64_encode(force_bytes(u.pk))
        token = default_token_generator.make_token(u)
        response = self.client.get(
            reverse("accounts:verify_email", args=[uid, token])
        )
        self.assertEqual(response.status_code, 302)
        u.refresh_from_db()
        self.assertTrue(u.is_active)
        self.assertTrue(u.email_verified)

    def test_duplicate_email_rejected(self):
        """UC01-03.
        Pre: alice@sky.example already exists.
        Steps: POST register with same email.
        Expected: 200 with form error, no second user created.
        Post: DB unchanged.
        Priority: MEDIUM.
        """
        User.objects.create_user("alice", email="alice@sky.example", password="x" * 12)
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "alice2",
                "email": "alice@sky.example",
                "full_name": "Alice Two",
                "password1": "S0lidPassw0rd!",
                "password2": "S0lidPassw0rd!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email="alice@sky.example").count(), 1)


class LoginAndLogoutTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            "carol", email="carol@sky.example", password="GoodPassword!1"
        )
        self.user.email_verified = True
        self.user.save()

    def test_login_with_correct_password_redirects_to_dashboard(self):
        """UC02-01.
        Pre: verified user.
        Steps: POST /accounts/login/ with right password.
        Expected: 302 to /dashboard/.
        Post: session created.
        Priority: HIGH.
        """
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "carol", "password": "GoodPassword!1"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard/", response["Location"])

    def test_unverified_user_blocked_at_login(self):
        """UC02-02.
        Pre: account with email_verified=False.
        Steps: POST /accounts/login/.
        Expected: 302 to resend-verification page, NOT to dashboard.
        Post: not authenticated.
        Priority: HIGH.
        """
        self.user.email_verified = False
        self.user.save()
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "carol", "password": "GoodPassword!1"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("resend", response["Location"])

    def test_logout_redirects_to_login(self):
        """UC02-03.
        Pre: user logged in.
        Steps: POST /accounts/logout/.
        Expected: 302 to /accounts/login/.
        Post: session destroyed.
        Priority: MEDIUM.
        """
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])


class PasswordValidatorTests(TestCase):
    """Custom validators in accounts/validators.py."""

    def _post(self, password):
        return self.client.post(
            reverse("accounts:register"),
            {
                "username": "weakpw",
                "email": "weakpw@sky.example",
                "full_name": "Weak Pw",
                "password1": password,
                "password2": password,
            },
        )

    def test_password_without_uppercase_rejected(self):
        """UC02-04. Pre: none. Steps: register with password
        'alllowercase1!'. Expected: 200 with 'uppercase' in errors,
        no user persisted. Priority: HIGH (security)."""
        r = self._post("alllowercase1!")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "uppercase")
        self.assertFalse(User.objects.filter(username="weakpw").exists())

    def test_password_without_symbol_rejected(self):
        """UC02-05. Pre: none. Steps: register with 'GoodPassword1'.
        Expected: 200 with 'symbol' in errors. Priority: HIGH."""
        r = self._post("GoodPassword1")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "symbol")

    def test_password_with_space_rejected(self):
        """UC02-06. Pre: none. Steps: register with 'Good Password1!'
        (contains a space). Expected: 200 with 'spaces' in errors.
        Priority: MEDIUM."""
        r = self._post("Good Password1!")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "spaces")

    def test_password_meeting_all_rules_accepted(self):
        """UC02-07. Pre: none. Steps: register with 'GoodPassword1!'.
        Expected: 302 redirect, user is created. Priority: HIGH."""
        r = self._post("GoodPassword1!")
        self.assertEqual(r.status_code, 302)
        self.assertTrue(User.objects.filter(username="weakpw").exists())


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "dan", email="dan@sky.example", password="S0lidPass!1"
        )
        self.user.email_verified = True
        self.user.save()
        self.client.force_login(self.user)

    def test_profile_view_renders_for_self(self):
        """UC03-01. Pre: logged in. Steps: GET /accounts/profile/.
        Expected: 200, page contains the user's full name. Priority: MEDIUM."""
        self.user.full_name = "Dan The Engineer"
        self.user.save()
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dan The Engineer")

    def test_profile_edit_persists_changes(self):
        """UC03-02. Pre: logged in. Steps: POST profile edit form with
        new job title. Expected: 302 + persisted job_title. Priority: MEDIUM."""
        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "full_name": "Dan Updated",
                "job_title": "Staff engineer",
                "email": "dan@sky.example",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.job_title, "Staff engineer")
