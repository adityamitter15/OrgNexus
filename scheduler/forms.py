# File: scheduler/forms.py - Aditya Mitter (W19869650)

from django import forms

from accounts.models import User

from .models import Meeting


class MeetingForm(forms.ModelForm):
    # Checkboxes are a bit verbose for ~240 users but together with the
    # client-side search box on the meeting_form template it's the best
    # readable picker we can build without adding a JS dependency.
    invitees = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by("full_name", "username"),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = Meeting
        fields = [
            "title",
            "date_time",
            "duration_minutes",
            "platform",
            "location_url",
            "agenda",
            "recurrence",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "date_time": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "duration_minutes": forms.NumberInput(attrs={"class": "form-control"}),
            "platform": forms.TextInput(attrs={"class": "form-control"}),
            "location_url": forms.URLInput(attrs={"class": "form-control"}),
            "agenda": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "recurrence": forms.Select(attrs={"class": "form-select"}),
        }
