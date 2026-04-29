# File: core/views.py - Aditya Mitter (W19869650)
"""Cross-cutting views: home, dashboard, global search, error pages."""

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render

from messaging.models import MessageRecipient
from organisation.models import Department
from reports.models import Project
from scheduler.models import Meeting
from teams.models import Team, TeamDependency
from accounts.models import User


def home(request):
    """Anonymous landing page. Authenticated users skip straight to /dashboard/."""
    if request.user.is_authenticated:
        return dashboard(request)
    return render(request, "core/home.html")


@login_required
def dashboard(request):
    """Top-level workspace - shows the four CW1 mockup tiles plus a
    'jump to recent' panel."""

    # We do all counts in one round trip per table to keep the page snappy.
    counts = {
        "departments": Department.objects.count(),
        "teams": Team.objects.count(),
        "engineers": User.objects.filter(is_active=True).count(),
        "dependencies": TeamDependency.objects.count(),
        "projects": Project.objects.count(),
    }

    # Inbox preview: three most recent unread items addressed to me.
    unread = (
        MessageRecipient.objects
        .filter(recipient=request.user, is_read=False, message__status="SENT")
        .select_related("message", "message__sender")
        .order_by("-message__sent_at", "-message__created_at")[:3]
    )

    # Upcoming meetings I'm invited to (or that I created).
    upcoming = (
        Meeting.objects
        .filter(Q(participants__user=request.user) | Q(created_by=request.user))
        .order_by("date_time")
        .distinct()[:5]
    )

    # Top departments by team count - drives the right-hand sidebar.
    top_depts = (
        Department.objects
        .annotate(num_teams=Count("teams"))
        .order_by("-num_teams")[:5]
    )

    return render(
        request,
        "core/dashboard.html",
        {
            "counts": counts,
            "unread": unread,
            "upcoming": upcoming,
            "top_depts": top_depts,
        },
    )


@login_required
def search(request):
    """Single search box on the navbar. Hits team / department / user
    in one query so the results page lists all three groups."""

    q = request.GET.get("q", "").strip()
    teams = depts = people = []
    if q:
        teams = (
            Team.objects.filter(
                Q(name__icontains=q)
                | Q(department__name__icontains=q)
                | Q(manager__full_name__icontains=q)
                | Q(slack_channel__icontains=q)
            )
            .select_related("department", "manager")
            .distinct()[:25]
        )
        depts = Department.objects.filter(
            Q(name__icontains=q) | Q(specialisation__icontains=q)
        )[:10]
        people = User.objects.filter(
            Q(full_name__icontains=q)
            | Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(job_title__icontains=q)
        )[:25]

    return render(
        request,
        "core/search_results.html",
        {"q": q, "teams": teams, "depts": depts, "people": people},
    )
