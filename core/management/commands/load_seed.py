# File: core/management/commands/load_seed.py - Aditya Mitter (W19869650)
"""Populate the database from Sky's team registry spreadsheet.

We read `04_team_data/team_registry.xlsx` (or any path passed in via
`--xlsx`) and create:
    - one Department per unique department in the sheet
    - one Team per row, with manager (Team Leader column) + dept head
    - a TeamType taken from the 'Dependency Type' column (rough but
      gives us a varied set of team types)
    - a User per unique person seen as Team Leader or Dept Head
    - a Staff row per team with five synthetic engineers (so we hit
      the brief's '>= 5 engineers per team' floor)
    - a TeamDependency row from the 'Downstream Dependencies' column
    - a few Projects per department for the analytics page

Run:
    python manage.py load_seed
    python manage.py load_seed --xlsx /custom/path.xlsx --reset
"""

import datetime as dt
import random
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from openpyxl import load_workbook

from organisation.models import Department, DepartmentHead, FocusArea
from reports.models import Project
from teams.models import (
    Skill,
    Staff,
    Team,
    TeamDependency,
    TeamLeader,
    TeamSkill,
    TeamType,
)

User = get_user_model()


_DEFAULT_XLSX = (
    Path(__file__).resolve().parents[4] / "04_team_data" / "team_registry.xlsx"
)


class Command(BaseCommand):
    help = "Seed OrgNexus from the Sky team-registry spreadsheet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--xlsx", default=str(_DEFAULT_XLSX),
            help="Path to the team registry .xlsx",
        )
        parser.add_argument(
            "--reset", action="store_true",
            help="Wipe existing seed rows before loading.",
        )
        parser.add_argument(
            "--engineers-per-team", type=int, default=5,
            help="How many synthetic Staff rows to add per team.",
        )
        parser.add_argument(
            "--max-teams-per-dept", type=int, default=3,
            help="Cap teams per department - default = brief minimum (3).",
        )
        parser.add_argument(
            "--max-departments", type=int, default=2,
            help="Cap departments loaded - default = brief minimum (2).",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        xlsx = Path(opts["xlsx"])
        if not xlsx.exists():
            self.stderr.write(f"Spreadsheet not found at {xlsx}")
            return

        if opts["reset"]:
            self._reset_seeded_rows()

        wb = load_workbook(xlsx, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        header, rows = rows[0], rows[1:]
        col = {name: idx for idx, name in enumerate(header) if name}

        # Brief asks for >= 2 dept, >= 3 teams/dept, >= 5 engineers/team.
        # We default to those exact minimums so the seeded scale doesn't
        # look implausible for a two-person student project. Bump via
        # the --max-teams-per-dept and --max-departments flags.
        from collections import Counter
        team_count = Counter()
        for row in rows:
            if row and row[col["Team Name"]] and row[col["Department"]]:
                team_count[row[col["Department"]].strip()] += 1

        # Need departments that have at least the configured team cap
        # available in the registry (so we don't end up short).
        min_teams = opts["max_teams_per_dept"]
        eligible = [d for d, n in team_count.items() if n >= min_teams]
        # Take the largest eligible departments first - more variety
        # in seeded teams than picking alphabetically.
        eligible.sort(key=lambda d: -team_count[d])
        keep_dept = set(eligible[:opts["max_departments"]])
        teams_taken = Counter()

        focus_default, _ = FocusArea.objects.get_or_create(
            name="Streaming platforms",
            defaults={"description": "Sky's primary streaming engineering practice."},
        )

        depts_made = {}
        types_made = {}
        users_made = {}
        teams_made = {}

        for row in rows:
            if not row or not row[col["Team Name"]]:
                continue
            row_dept = (row[col["Department"]] or "").strip()
            if row_dept not in keep_dept:
                continue
            # Stop adding teams to a dept once we've hit the cap.
            if teams_taken[row_dept] >= opts["max_teams_per_dept"]:
                continue
            teams_taken[row_dept] += 1

            dept_name = (row[col["Department"]] or "").strip()
            team_name = (row[col["Team Name"]] or "").strip()
            leader_name = (row[col["Team Leader"]] or "").strip()
            head_name = (row[col["Department Head"]] or "").strip()
            focus_text = (row[col["Development Focus Areas"]] or "").strip()
            github = (row[col["Project (codebase) (Github Repo)"]] or "").strip()
            jira = (row[col["Jira board Link"]] or "").strip()
            workstream = (row[col["Jira Project Name"]] or "").strip()
            slack = _coerce_text(row[col["Slack Channels"]] if col.get(
                "Slack Channels") is not None else "")
            standup = _coerce_text(row[col["Daily Standup Time and Link"]] if col.get(
                "Daily Standup Time and Link") is not None else "")
            agile = _coerce_text(row[col["Agile Practices"]] if col.get(
                "Agile Practices") is not None else "")
            dep_type = (row[col["Dependency Type"]] or "").strip()
            # downstream_name is read in pass 2 directly off the row,
            # so we don't need a local for it here.
            skills_blob = (row[col["Key Skills & Technologies"]] or "").strip()

            if not dept_name or not team_name:
                continue

            dept = depts_made.get(dept_name)
            if not dept:
                dept, _ = Department.objects.get_or_create(
                    name=dept_name,
                    defaults={
                        "specialisation": workstream,
                        "description": f"{dept_name} engineering at Sky.",
                        "focus_area": focus_default,
                    },
                )
                depts_made[dept_name] = dept

            team_type = None
            if dep_type:
                team_type = types_made.get(dep_type)
                if not team_type:
                    team_type, _ = TeamType.objects.get_or_create(type_name=dep_type)
                    types_made[dep_type] = team_type

            manager = self._user(leader_name, users_made)
            head_user = self._user(head_name, users_made)

            team, created = Team.objects.get_or_create(
                name=team_name, department=dept,
                defaults={
                    "team_type": team_type,
                    "manager": manager,
                    "mission": focus_text or "Mission TBC.",
                    "description": (
                        f"Auto-seeded from the team registry. Workstream: {workstream}."
                    ),
                    "github_repo": _safe_url(github),
                    "jira_link": _safe_url(jira),
                    "slack_channel": (slack or f"#{slugify(team_name)}")[:79],
                    "contact_email": f"{slugify(team_name)}@sky.example",
                    "standup_time": standup,
                    "agile_practices": agile,
                },
            )
            teams_made[team_name] = team
            if not created:
                continue

            # Department head row (one active head per dept).
            if head_user and not DepartmentHead.objects.filter(
                department=dept, stepped_down__isnull=True
            ).exists():
                DepartmentHead.objects.create(
                    user=head_user,
                    department=dept,
                    appointed=dt.date.today() - dt.timedelta(days=365),
                )

            # Team leader.
            if manager:
                TeamLeader.objects.get_or_create(
                    user=manager, team=team,
                    defaults={"appointed": dt.date.today() - dt.timedelta(days=180)},
                )
                Staff.objects.get_or_create(
                    user=manager, team=team,
                    defaults={"role": "Lead engineer"},
                )

            # Synthetic engineers - need at least 5 per team per the brief.
            engineers_needed = opts["engineers_per_team"]
            existing = team.staff.count()
            for n in range(existing, engineers_needed):
                eng_username = slugify(f"{team_name}-eng-{n + 1}")[:148]
                eng, _ = User.objects.get_or_create(
                    username=eng_username,
                    defaults={
                        "email": f"{eng_username}@sky.example",
                        "full_name": _fake_name(eng_username),
                        "job_title": "Software engineer",
                        "is_active": True,
                        "email_verified": True,
                    },
                )
                Staff.objects.get_or_create(user=eng, team=team)

            # Skills (split the comma-separated blob).
            for raw in (skills_blob or "").split(","):
                name = raw.strip()
                if not name:
                    continue
                skill, _ = Skill.objects.get_or_create(name=name[:80])
                TeamSkill.objects.get_or_create(team=team, skill=skill)

        # Pass 2: dependencies (need both ends to exist already).
        for row in rows:
            if not row or not row[col["Team Name"]]:
                continue
            up_name = (row[col["Team Name"]] or "").strip()
            down_name = (row[col["Downstream Dependencies"]] or "").strip()
            dep_type = (row[col["Dependency Type"]] or "").strip()
            if not up_name or not down_name:
                continue
            up = teams_made.get(up_name)
            down = teams_made.get(down_name)
            if not up or not down or up == down:
                continue
            TeamDependency.objects.get_or_create(
                upstream=up,
                downstream=down,
                defaults={
                    "dependency_type": _normalise_dep_type(dep_type),
                    "description": f"Seeded from registry: {dep_type}.",
                },
            )

        # A handful of Projects per department for the analytics page.
        rng = random.Random(42)
        statuses = [Project.PLANNED, Project.ACTIVE, Project.PAUSED, Project.DONE]
        for dept in depts_made.values():
            existing = dept.projects.count()
            for n in range(existing, max(3, existing + 3)):
                Project.objects.create(
                    name=f"{dept.name} initiative {n + 1}",
                    description="Seeded sample project.",
                    department=dept,
                    status=rng.choice(statuses),
                    started_on=dt.date.today() - dt.timedelta(days=rng.randint(30, 400)),
                )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(depts_made)} departments, "
            f"{len(teams_made)} teams, "
            f"{User.objects.count()} users."
        ))

    def _user(self, full_name, cache):
        if not full_name:
            return None
        full_name = full_name.strip()
        if full_name in cache:
            return cache[full_name]
        username = slugify(full_name).replace("-", "")[:30] or f"u{len(cache)}"
        # Username must be unique - bump if collisions.
        base = username
        n = 2
        while User.objects.filter(username=username).exists():
            username = f"{base}{n}"[:150]
            n += 1
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "email": f"{username}@sky.example",
                "full_name": full_name,
                "job_title": "Engineering",
                "is_active": True,
                "email_verified": True,
            },
        )
        cache[full_name] = user
        return user

    def _reset_seeded_rows(self):
        # Wipes everything except superusers.
        Project.objects.all().delete()
        TeamDependency.objects.all().delete()
        TeamSkill.objects.all().delete()
        Skill.objects.all().delete()
        TeamLeader.objects.all().delete()
        Staff.objects.all().delete()
        Team.objects.all().delete()
        TeamType.objects.all().delete()
        DepartmentHead.objects.all().delete()
        Department.objects.all().delete()
        FocusArea.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()


def _coerce_text(value):
    """Spreadsheet cells can be None / numbers / dates - turn anything
    into a stripped string and drop the broken Excel #REF! tokens."""
    if value is None:
        return ""
    text = str(value).strip()
    if "#REF!" in text:
        return ""
    return text


def _safe_url(value):
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    return f"https://{value}"


def _normalise_dep_type(raw):
    raw = (raw or "").lower()
    if "data" in raw:
        return "DATA"
    if "platform" in raw or "infra" in raw:
        return "PLATFORM"
    if "api" in raw:
        return "API"
    return "OTHER"


_FIRST = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Riley", "Drew", "Casey",
         "Reese", "Quinn", "Skyler", "Dylan"]
_LAST = ["Adams", "Brooks", "Carter", "Diaz", "Evans", "Fisher", "Grant",
         "Hughes", "Iyer", "Jensen", "Khan", "Lopez"]


def _fake_name(seed):
    rng = random.Random(seed)
    return f"{rng.choice(_FIRST)} {rng.choice(_LAST)}"
