# File: teams/forms.py - Aditya Mitter (W19869650)

from django import forms

from .models import Team, TeamDependency


def _bootstrapify(form):
    for name, field in form.fields.items():
        widget = field.widget
        if isinstance(widget, forms.Select):
            widget.attrs.setdefault("class", "form-select")
        elif isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault("class", "form-check-input")
        else:
            widget.attrs.setdefault("class", "form-control")


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = [
            "name",
            "department",
            "team_type",
            "manager",
            "mission",
            "description",
            "github_repo",
            "jira_link",
            "confluence_link",
            "slack_channel",
            "teams_channel",
            "contact_email",
            "standup_time",
            "agile_practices",
            "num_concurrent_projects",
        ]
        widgets = {
            "mission": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)


class TeamDependencyForm(forms.ModelForm):
    class Meta:
        model = TeamDependency
        fields = ["upstream", "downstream", "dependency_type", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self)

    def clean(self):
        cleaned = super().clean()
        up = cleaned.get("upstream")
        down = cleaned.get("downstream")
        # Form-level guard - the DB has a CHECK constraint too, but a
        # clean validation error reads better than an IntegrityError.
        if up and down and up == down:
            raise forms.ValidationError("A team cannot depend on itself.")
        return cleaned
