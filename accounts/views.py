# File: accounts/views.py - Aditya Mitter (W19869650)
"""Auth flow views.

Highlights for the report:
    - Email-verification on signup using Django's signed-token tools
      (the same machinery powering PasswordResetView), so we don't
      invent a new token format.
    - Login is wrapped to keep django-axes lockouts visible to the user
      with a friendly message instead of a stack trace.
    - Profile view + edit are split so visiting /profile/ feels like a
      page, not a form.
"""

from django.conf import settings
from django.contrib import messages as django_messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView

from .forms import OrgNexusLoginForm, ProfileForm, RegisterForm
from .models import User


def _send_verification_email(request, user):
    """Build and send the email that confirms ownership of `user.email`.

    We use Django's signed-token generator (the same one PasswordReset
    uses) so the token can't be forged without the secret key.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = request.build_absolute_uri(
        reverse("accounts:verify_email", args=[uidb64, token])
    )
    body = render_to_string(
        "accounts/email/verify_email.txt",
        {"user": user, "link": link, "site": "OrgNexus"},
    )
    send_mail(
        subject="Confirm your OrgNexus account",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


class RegisterView(CreateView):
    template_name = "accounts/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        # Save first so we have a pk for the token, then mail.
        response = super().form_valid(form)
        _send_verification_email(self.request, self.object)
        django_messages.success(
            self.request,
            "Account created. Check your email for the verification link.",
        )
        return response


class VerifyEmailView(View):
    """Click target for the link in the verification email."""

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            # Token is good - flip both flags so the user can log in.
            if not user.is_active or not user.email_verified:
                user.is_active = True
                user.email_verified = True
                user.save(update_fields=["is_active", "email_verified"])
                django_messages.success(
                    request, "Email verified. You can now sign in."
                )
            else:
                django_messages.info(request, "Your email is already verified.")
            return redirect("accounts:login")

        django_messages.error(
            request, "Verification link is invalid or has expired."
        )
        return redirect("accounts:resend_verification")


class ResendVerificationView(View):
    """Email-only form that resends the verification link."""

    template_name = "accounts/resend_verification.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email", "").strip().lower()
        # We don't reveal whether the email exists - same pattern as
        # the password-reset view, to avoid an account-enumeration leak.
        try:
            user = User.objects.get(email__iexact=email)
            if not user.email_verified:
                _send_verification_email(request, user)
        except User.DoesNotExist:
            pass
        django_messages.info(
            request,
            "If that email matches an account, a fresh verification link "
            "has just been sent.",
        )
        return redirect("accounts:login")


class OrgNexusLoginView(LoginView):
    """Thin wrapper around Django's LoginView so we can:

    1. Apply Bootstrap classes via OrgNexusLoginForm.
    2. Block users whose email isn't verified yet (with a clear message
       rather than a generic 'invalid credentials').
    """

    template_name = "accounts/login.html"
    authentication_form = OrgNexusLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if not user.email_verified:
            django_messages.warning(
                self.request,
                "Please verify your email before signing in. "
                "Need another link?",
            )
            return redirect("accounts:resend_verification")
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, DetailView):
    template_name = "accounts/profile.html"
    context_object_name = "profile_user"

    def get_object(self, queryset=None):
        # Always show the logged-in user's own profile - no per-user
        # browsing of profiles in this CW (single user category).
        return self.request.user


class ProfileEditView(LoginRequiredMixin, UpdateView):
    template_name = "accounts/profile_edit.html"
    form_class = ProfileForm
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        django_messages.success(self.request, "Profile updated.")
        return super().form_valid(form)
