# File: core/management/commands/email_test.py - Aditya Mitter (W19869650)
"""Sanity-check the configured email backend.

Sends a one-line message to the address given on the command line so we
can verify Resend (or any other backend) is wired correctly without
having to walk the password-reset flow.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send a test email through the configured backend."

    def add_arguments(self, parser):
        parser.add_argument("--to", required=True, help="Recipient address.")
        parser.add_argument(
            "--subject", default="OrgNexus email test",
            help="Subject line (default: 'OrgNexus email test').",
        )

    def handle(self, *args, **opts):
        backend = settings.EMAIL_BACKEND.rsplit(".", 1)[-1]
        self.stdout.write(f"Using {backend} via {settings.EMAIL_HOST}.")
        sent = send_mail(
            subject=opts["subject"],
            message=(
                "If you can read this email, OrgNexus is wired up to send "
                "verification + password-reset messages."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[opts["to"]],
            fail_silently=False,
        )
        self.stdout.write(self.style.SUCCESS(
            f"send_mail returned {sent}. Check the recipient inbox."
        ))
