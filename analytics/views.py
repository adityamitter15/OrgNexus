# File: analytics/views.py - Aditya Mitter (W19869650)
"""Chart.js endpoints. The HTML page renders the canvases; the JSON
endpoints feed them with tidy data so we don't inline blobs in the page."""

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render

from organisation.models import Department


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
        {
            "labels": [d.name for d in rows],
            "values": [d.num_teams for d in rows],
        }
    )


@login_required
def projects_per_dept_data(request):
    rows = (
        Department.objects.annotate(num_projects=Count("projects"))
        .order_by("-num_projects", "name")
    )
    return JsonResponse(
        {
            "labels": [d.name for d in rows],
            "values": [d.num_projects for d in rows],
        }
    )
