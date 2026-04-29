# File: core/middleware.py - Aditya Mitter (W19869650)
"""Tiny middleware that stashes the current user on a thread-local so
the audit-log signals can pick up who did the action.

Django signals don't see the request object, so without this every
AuditLog row would have actor=NULL. Threadlocals are the standard
work-around (also used by django-simple-history etc.).
"""

import threading


_local = threading.local()


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.user = getattr(request, "user", None)
        try:
            return self.get_response(request)
        finally:
            # Clear after each request so a cached worker can't leak
            # one user's identity into another's signal callback.
            _local.user = None


def get_current_user():
    user = getattr(_local, "user", None)
    if user and getattr(user, "is_authenticated", False):
        return user
    return None
