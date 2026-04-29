# File: accounts/validators.py - Aditya Mitter (W19869650)
"""High-end password validators wired into AUTH_PASSWORD_VALIDATORS.

Each class follows Django's validator protocol:
    - validate(password, user=None) -> raises ValidationError if it fails
    - get_help_text() -> the line shown beside the password field
"""

import re
import string

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class UppercaseValidator:
    """At least one uppercase letter (A-Z)."""

    def validate(self, password, user=None):
        if not re.search(r"[A-Z]", password or ""):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code="password_no_uppercase",
            )

    def get_help_text(self):
        return _("Must contain at least one uppercase letter (A-Z).")


class LowercaseValidator:
    """At least one lowercase letter (a-z)."""

    def validate(self, password, user=None):
        if not re.search(r"[a-z]", password or ""):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code="password_no_lowercase",
            )

    def get_help_text(self):
        return _("Must contain at least one lowercase letter (a-z).")


class DigitValidator:
    """At least one digit (0-9)."""

    def validate(self, password, user=None):
        if not re.search(r"[0-9]", password or ""):
            raise ValidationError(
                _("Password must contain at least one digit."),
                code="password_no_digit",
            )

    def get_help_text(self):
        return _("Must contain at least one digit (0-9).")


class SymbolValidator:
    """At least one symbol from a printable, non-alphanumeric set."""

    SYMBOLS = string.punctuation  # !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~

    def validate(self, password, user=None):
        if not any(ch in self.SYMBOLS for ch in (password or "")):
            raise ValidationError(
                _("Password must contain at least one symbol "
                  "(e.g. ! @ # $ % & * ?)."),
                code="password_no_symbol",
            )

    def get_help_text(self):
        return _("Must contain at least one symbol such as ! @ # $ % & * ?.")


class NoSpacesValidator:
    """Reject whitespace - users tend to copy-paste passwords with
    leading/trailing spaces and then can't log in. Surfacing it as a
    rule is friendlier than silently stripping."""

    def validate(self, password, user=None):
        if password and re.search(r"\s", password):
            raise ValidationError(
                _("Password must not contain spaces or tabs."),
                code="password_has_whitespace",
            )

    def get_help_text(self):
        return _("Must not contain spaces or tabs.")
