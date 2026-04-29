# File: orgnexus/settings.py - Aditya Mitter (W19869650)
"""Project settings for OrgNexus.

This file is the single place we configure Django, security, the auth
flow and our app list. Inline comments call out the choices we want to
explain in the GROUP report (security risks register, maintainability,
HCI consistency).
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# In a real deployment the secret would come from an env var; for the
# laptop demo we keep a local default but still allow override so the
# README can show how to change it.
SECRET_KEY = os.environ.get(
    "ORGNEXUS_SECRET_KEY",
    "django-insecure-dev-only-do-not-use-this-in-production-orgnexus-2026",
)

# Toggle DEBUG=False before recording the demo so the marker sees a
# clean error page instead of the development traceback.
DEBUG = os.environ.get("ORGNEXUS_DEBUG", "1") == "1"

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]


# --- Apps -----------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Brute-force protection on the login form.
    "axes",

    # OrgNexus apps.
    "accounts.apps.AccountsConfig",
    "organisation.apps.OrganisationConfig",
    "teams.apps.TeamsConfig",
    "messaging.apps.MessagingConfig",
    "scheduler.apps.SchedulerConfig",
    "reports.apps.ReportsConfig",
    "analytics.apps.AnalyticsConfig",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # axes goes last so it sees authenticate() failures.
    "axes.middleware.AxesMiddleware",

    # Stash request.user on a threadlocal so audit signals can read it.
    "core.middleware.CurrentUserMiddleware",
]

ROOT_URLCONF = "orgnexus.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.debug_flag",
            ],
        },
    },
]

WSGI_APPLICATION = "orgnexus.wsgi.application"


# --- Database -------------------------------------------------------------

# SQLite is mandated by the brief - good for a single-laptop demo, not
# great for prod (we mention this honestly in the security section).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# --- Custom user model ---------------------------------------------------

# This MUST be set before the first migrate. Trying to swap it later
# is a documented Django pain point so we lock it in early.
AUTH_USER_MODEL = "accounts.User"


# --- Authentication backends ---------------------------------------------

# Order matters: axes' backend short-circuits before Django's so it can
# count failures, then Django's default backend does the actual lookup.
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "accounts.backends.UsernameOrEmailBackend",
]


# --- Password hashing & validation ---------------------------------------

# PBKDF2 is Django's secure default; argon2 is even stronger but needs a
# C library so we leave it commented for now.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    # Django built-ins.
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        # OWASP Application Security Verification Standard recommends
        # >= 12 for memorised secrets - we land at 10 to balance demo-day
        # convenience and security marks.
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},

    # OrgNexus extras (see accounts/validators.py).
    {"NAME": "accounts.validators.UppercaseValidator"},
    {"NAME": "accounts.validators.LowercaseValidator"},
    {"NAME": "accounts.validators.DigitValidator"},
    {"NAME": "accounts.validators.SymbolValidator"},
    {"NAME": "accounts.validators.NoSpacesValidator"},
]


# --- Login / logout redirects -------------------------------------------

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"


# --- Cookie & header hardening ------------------------------------------

# These cover the OWASP-style risks we list in the group report.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 hours - matches a Sky working day.
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# When DEBUG is off (demo recording), force secure cookies.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# --- django-axes (brute-force lockout) ----------------------------------

AXES_FAILURE_LIMIT = 5          # five wrong passwords...
AXES_COOLOFF_TIME = 0.5         # ...locks the account for 30 minutes.
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = ["username"]


# --- Email backend -------------------------------------------------------

# Three modes, picked by env var:
#   1. RESEND_API_KEY set         -> SMTP through Resend's gateway. Real
#                                    emails arrive in the user's inbox.
#   2. ORGNEXUS_EMAIL_BACKEND set -> manual override (any Django backend).
#   3. neither set                -> file backend writing to dev_outbox/
#                                    so the marker can read messages in
#                                    the browser at /accounts/dev/outbox/.
DEV_OUTBOX = BASE_DIR / "dev_outbox"
DEV_OUTBOX.mkdir(exist_ok=True)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

if RESEND_API_KEY and not os.environ.get("ORGNEXUS_EMAIL_BACKEND"):
    # Resend's SMTP gateway: smtp.resend.com:587 with STARTTLS,
    # username literal "resend", password = the API key.
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.resend.com"
    EMAIL_PORT = 587
    EMAIL_HOST_USER = "resend"
    EMAIL_HOST_PASSWORD = RESEND_API_KEY
    EMAIL_USE_TLS = True
else:
    EMAIL_BACKEND = os.environ.get(
        "ORGNEXUS_EMAIL_BACKEND",
        "django.core.mail.backends.filebased.EmailBackend",
    )
    EMAIL_HOST = os.environ.get("ORGNEXUS_EMAIL_HOST", "smtp.resend.com")
    EMAIL_PORT = int(os.environ.get("ORGNEXUS_EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("ORGNEXUS_EMAIL_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("ORGNEXUS_EMAIL_PASS", "")
    EMAIL_USE_TLS = os.environ.get("ORGNEXUS_EMAIL_TLS", "1") == "1"

EMAIL_FILE_PATH = str(DEV_OUTBOX)
DEFAULT_FROM_EMAIL = os.environ.get(
    "ORGNEXUS_FROM_EMAIL", "OrgNexus <onboarding@resend.dev>"
)

# Password-reset tokens expire after three days (Django default is one,
# we bump it slightly so users have time over a weekend).
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 3


# --- i18n / tz ----------------------------------------------------------

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True


# --- Static & media files -----------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# --- Misc ---------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# We log admin-relevant events so the report can show audit-evidence
# beyond the AuditLog table.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "django.security": {"handlers": ["console"], "level": "INFO"},
        "axes": {"handlers": ["console"], "level": "INFO"},
    },
}
