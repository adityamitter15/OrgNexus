# File: accounts/models.py - Aditya Mitter (W19869650)
"""User model for OrgNexus.

The brief says single user category, so the only thing we extend on top
of Django's AbstractUser is the profile fields the marker pointed out
were missing in CW1 (full_name, job_title, avatar) plus an explicit
email_verified flag we use for the email-confirmation flow.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # We use email as the second key the user signs up with, so make
    # sure it's unique - Django's default AbstractUser allows duplicates.
    email = models.EmailField(unique=True)

    full_name = models.CharField(max_length=120, blank=True)
    job_title = models.CharField(max_length=120, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    # Set to True once the user clicks the verification link we email
    # them on signup. We block login until this is True.
    email_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["username"]

    def __str__(self):
        # Prefer the full name so the admin and message lists read nicely;
        # fall back to the username so we never render a blank label.
        return self.full_name or self.username

    def get_display_name(self):
        return self.full_name or self.username
