# File: scheduler/forms.py - Aditya Mitter (W19869650)

from django import forms

from accounts.models import User

from .models import Meeting


class MeetingForm(forms.ModelForm):
    invitees = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
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
