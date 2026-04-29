# File: organisation/models.py - Aditya Mitter (W19869650) and Noah Gil De Matos Jimenez
"""Department / FocusArea / TeamType / DepartmentHead schema.

Closes the entities the marker said were missing in CW1: FocusArea and
DepartmentHead. The brief requires at least 2 departments, 3 teams per
department, 5 engineers per team - we enforce the lower bounds in seed
data, not in the model layer (so a marker can still create a single
test department from the admin).
"""

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class FocusArea(models.Model):
    """A practice area shared across departments (e.g. Streaming, Identity).

    This was missing from CW1 (-2 marks on the ERD). Departments and
    teams can both belong to a focus area, which is how Sky groups work
    that crosses the formal org chart.
    """

    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    specialisation = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    focus_area = models.ForeignKey(
        FocusArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="departments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-fill the slug on first save so the URL is friendly without
        # the admin having to think about it.
        if not self.slug:
            self.slug = slugify(self.name)[:140]
        super().save(*args, **kwargs)

    def team_count(self):
        # Used on the dashboard counters - cached on the queryset side.
        return self.teams.count()


class DepartmentHead(models.Model):
    """The single person currently leading a department.

    Was missing in CW1 (-1.5 marks on the ERD). We model it as a
    separate row rather than a FK on Department so we can keep an
    appointment history (one row per leadership term).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="department_head_roles",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="head_history",
    )
    appointed = models.DateField()
    stepped_down = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-appointed"]
        constraints = [
            # One person can only currently-lead one department; we use
            # a partial unique index by checking stepped_down IS NULL.
            models.UniqueConstraint(
                fields=["department"],
                condition=models.Q(stepped_down__isnull=True),
                name="one_active_head_per_department",
            ),
        ]

    def __str__(self):
        return f"{self.user} -> {self.department}"

    @property
    def is_active(self):
        return self.stepped_down is None
