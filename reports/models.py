# File: reports/models.py - Aditya Mitter (W19869650)
"""Project entity used by the reports + analytics views.

The brief's 'Reports' page lists 'number of teams', 'summary' and
'teams without managers'. The 'analytics' app then visualises Project
counts per Department - that's why Project lives here in reports/
rather than in teams/.
"""

from django.conf import settings
from django.db import models


class Project(models.Model):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    DONE = "DONE"
    PAUSED = "PAUSED"
    STATUS_CHOICES = [
        (PLANNED, "Planned"),
        (ACTIVE, "Active"),
        (PAUSED, "Paused"),
        (DONE, "Done"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        "organisation.Department",
        on_delete=models.CASCADE,
        related_name="projects",
    )
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects_led",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PLANNED)
    started_on = models.DateField(null=True, blank=True)
    ended_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-started_on", "name"]

    def __str__(self):
        return self.name
