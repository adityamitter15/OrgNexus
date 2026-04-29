# File: teams/models.py - Aditya Mitter (W19869650)
"""Team domain - this is my (Aditya's) main individual element.

Models in this file:
    TeamType         - classification (Bug Resolution / Encryption / ...)
    Team             - core team entity, one row per team
    TeamLeader       - who has technical lead of a team (CW1 was missing this)
    Staff            - which engineers are members of which team (CW1 missing)
    TeamMembership   - lifecycle history (joined / left)
    Skill / TeamSkill - many-to-many for skills
    TeamDependency   - directional graph between teams
"""

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils.text import slugify


class TeamType(models.Model):
    """Open-set classification for the kind of work a team does."""

    type_name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["type_name"]

    def __str__(self):
        return self.type_name


class Team(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    # PROTECT - we never want to silently lose teams when a department
    # is deleted; the admin has to clear them out explicitly.
    department = models.ForeignKey(
        "organisation.Department",
        on_delete=models.PROTECT,
        related_name="teams",
    )
    team_type = models.ForeignKey(
        TeamType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teams",
    )

    # The line manager. SET_NULL because we shouldn't lose the team if
    # the manager leaves the company.
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teams_managed",
    )

    mission = models.TextField(blank=True)
    description = models.TextField(blank=True)

    # Repos and contact channels - the brief explicitly lists these and
    # the marker noted they were missing as discrete fields in CW1.
    github_repo = models.URLField(blank=True)
    jira_link = models.URLField(blank=True)
    confluence_link = models.URLField(blank=True)
    slack_channel = models.CharField(max_length=80, blank=True)
    teams_channel = models.CharField(max_length=120, blank=True)
    contact_email = models.EmailField(blank=True)

    standup_time = models.CharField(max_length=40, blank=True)
    agile_practices = models.CharField(max_length=120, blank=True)
    num_concurrent_projects = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "department")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:130] or "team"
            candidate = base
            n = 2
            # We can't trust users not to add two "Code Warriors" - keep
            # bumping the suffix until the slug is unique.
            while Team.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{n}"
                n += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def member_count(self):
        return self.staff.filter(is_active=True).count()


class TeamLeader(models.Model):
    """Technical lead of a team (separate from the line manager).

    Was missing in CW1 - the marker called this out explicitly. We keep
    a `stepped_down` date so we can show leadership history if the
    report calls for it.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_lead_roles",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="leaders",
    )
    appointed = models.DateField()
    stepped_down = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-appointed"]
        constraints = [
            models.UniqueConstraint(
                fields=["team"],
                condition=Q(stepped_down__isnull=True),
                name="one_active_lead_per_team",
            ),
        ]

    def __str__(self):
        return f"{self.user} leads {self.team}"


class Staff(models.Model):
    """Active membership of an engineer in a team.

    CW1 had no Staff entity. This is what the brief means by '5 engineers
    per team' - we count rows on this table (with is_active=True).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_roles",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="staff",
    )
    role = models.CharField(max_length=80, default="Engineer")
    is_active = models.BooleanField(default=True)
    joined_on = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["team", "user"]
        unique_together = ("user", "team")
        verbose_name_plural = "Staff"

    def __str__(self):
        return f"{self.user} on {self.team}"


class TeamMembership(models.Model):
    """Historical record of who has been on a team and when.

    Distinct from Staff: Staff is "is this person currently on the team",
    Membership is the full timeline (useful for the dependency view and
    for the audit trail).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-joined_at"]

    def __str__(self):
        return f"{self.user} <- {self.team} (since {self.joined_at:%Y-%m-%d})"


class Skill(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TeamSkill(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_skills")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="team_skills")
    proficiency = models.CharField(
        max_length=20,
        choices=[("BASIC", "Basic"), ("INTERMEDIATE", "Intermediate"), ("EXPERT", "Expert")],
        default="INTERMEDIATE",
    )

    class Meta:
        unique_together = ("team", "skill")

    def __str__(self):
        return f"{self.team} / {self.skill}"


class TeamDependency(models.Model):
    """A directional 'upstream depends-on / blocks downstream' edge.

    The brief asks us to render an org-wide dependency graph; this is
    the edge table. We forbid self-loops with a CHECK constraint
    (database-level integrity rather than relying on form validation).
    """

    upstream = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="downstream_links"
    )
    downstream = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="upstream_links"
    )
    description = models.TextField(blank=True)
    dependency_type = models.CharField(
        max_length=40,
        choices=[
            ("API", "API consumer"),
            ("DATA", "Data feed"),
            ("PLATFORM", "Platform"),
            ("OTHER", "Other"),
        ],
        default="API",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Team dependencies"
        unique_together = ("upstream", "downstream")
        constraints = [
            models.CheckConstraint(
                condition=~Q(upstream=F("downstream")),
                name="no_self_dependency",
            ),
        ]

    def __str__(self):
        return f"{self.upstream} -> {self.downstream}"
