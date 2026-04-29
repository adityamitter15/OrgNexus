# File: accounts/forms.py - Aditya Mitter (W19869650)
"""ModelForm + auth forms wired with Bootstrap classes."""

from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

from .models import User


_BOOTSTRAP_INPUT = {"class": "form-control"}
_BOOTSTRAP_FILE = {"class": "form-control"}


def _bootstrap_widgets(form):
    """Apply Bootstrap classes to every visible widget on a form.

    We do this in one place rather than repeating the attrs={'class': ...}
    pattern on every widget - keeps form definitions short.
    """
    for name, field in form.fields.items():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault("class", "form-check-input")
        elif isinstance(widget, forms.Select):
            widget.attrs.setdefault("class", "form-select")
        elif isinstance(widget, forms.FileInput):
            widget.attrs.setdefault("class", "form-control")
        else:
            widget.attrs.setdefault("class", "form-control")


class RegisterForm(UserCreationForm):
    """Self-registration form. We require email + full name + a 10-char
    password (validators are configured in settings.py)."""

    email = forms.EmailField(required=True, help_text="Work email - used for login.")
    full_name = forms.CharField(max_length=120, required=True)
    job_title = forms.CharField(max_length=120, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "full_name", "job_title", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widgets(self)

    def clean_email(self):
        # Belt-and-braces - the model has unique=True but a clear form
        # error reads better than the database integrity error.
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.full_name = self.cleaned_data.get("full_name", "")
        user.job_title = self.cleaned_data.get("job_title", "")
        # Stays inactive until they click the verification link.
        user.is_active = False
        user.email_verified = False
        if commit:
            user.save()
        return user


class OrgNexusLoginForm(AuthenticationForm):
    """We swap to email-or-username login by leaving the field name as
    'username' but accepting either - the lookup happens in the view."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Username or work email"
        _bootstrap_widgets(self)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("full_name", "job_title", "email", "avatar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widgets(self)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        # Allow keeping the same email; only block if another user owns it.
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Another account is using this email.")
        return email


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widgets(self)


class StyledPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widgets(self)


class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_widgets(self)
