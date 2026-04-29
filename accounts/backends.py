# File: accounts/backends.py - Aditya Mitter (W19869650)
"""Auth backend that lets users sign in with either their username
or their email. Bolted on top of Django's ModelBackend so we keep
permission lookups and the password hasher chain unchanged."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if not username or not password:
            return None

        # Username first - it's indexed and the common case.
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            # Fall through to email lookup so people can type either.
            try:
                user = UserModel.objects.get(email__iexact=username)
            except UserModel.DoesNotExist:
                # Run the default hasher anyway so timing doesn't leak
                # whether the username/email exists.
                UserModel().set_password(password)
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
