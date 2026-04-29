# File: analytics/views.py - Aditya Mitter (W19869650)
"""Chart.js endpoints. The HTML page draws the canvases, the JSON
endpoints feed them. Keeping data and view separate means the marker
can hit /analytics/data/... and inspect the raw figures."""

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render

from organisation.models import Department
from reports.models import Project
from teams.models import TeamType


@login_required
def charts(request):
    return render(request, "analytics/charts.html")


@login_required
def teams_per_dept_data(request):
    rows = (
        Department.objects.annotate(num_teams=Count("teams"))
        .order_by("-num_teams", "name")
    )
    return JsonResponse(
        {"labels": [d.name for d in rows], "values": [d.num_teams for d in rows]}
    )


@login_required
def projects_per_dept_data(request):
    rows = (
        Department.objects.annotate(num_projects=Count("projects"))
        .order_by("-num_projects", "name")
    )
    return JsonResponse(
        {"labels": [d.name for d in rows], "values": [d.num_projects for d in rows]}
    )


@login_required
def team_types_data(request):
    rows = (
        TeamType.objects.annotate(num_teams=Count("teams"))
        .filter(num_teams__gt=0)
        .order_by("-num_teams")
    )
    return JsonResponse(
        {"labels": [t.type_name for t in rows], "values": [t.num_teams for t in rows]}
    )


@login_required
def project_status_data(request):
    rows = (
        Project.objects.values("status")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    label_map = dict(Project.STATUS_CHOICES)
    return JsonResponse(
        {
            "labels": [label_map.get(r["status"], r["status"]) for r in rows],
            "values": [r["n"] for r in rows],
        }
    )
