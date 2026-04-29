# File: core/context_processors.py - Aditya Mitter (W19869650)
"""Adds settings.DEBUG into every template context as `debug`. Lets us
show the dev-outbox link without poking at INTERNAL_IPS."""

from django.conf import settings


def debug_flag(request):
    return {"debug": settings.DEBUG}
