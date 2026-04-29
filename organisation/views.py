# File: organisation/views.py - Noah Gil De Matos Jimenez (with Aditya base scaffolding)
"""Organisation menu - departments, team types, focus areas, full org tree."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Prefetch
from django.views.generic import DetailView, ListView, TemplateView

from teams.models import Team, TeamType

from .models import Department, FocusArea


class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = "organisation/department_list.html"
    context_object_name = "departments"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(num_teams=Count("teams"))
            .order_by("name")
        )


class DepartmentDetailView(LoginRequiredMixin, DetailView):
    model = Department
    template_name = "organisation/department_detail.html"
    context_object_name = "department"
    slug_field = "slug"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Prefetch teams + their managers so the tile grid renders in
        # one query.
        ctx["teams"] = (
            ctx["department"].teams.select_related("manager", "team_type").all()
        )
        ctx["projects"] = ctx["department"].projects.all()[:10]
        ctx["heads"] = (
            ctx["department"].head_history.select_related("user")
            .filter(stepped_down__isnull=True)
        )
        return ctx


class OrgStructureView(LoginRequiredMixin, TemplateView):
    """Full org tree as nested cards (works without JS so the marker
    can read it even if Mermaid fails to render)."""

    template_name = "organisation/org_structure.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        teams_qs = Team.objects.select_related("manager")
        ctx["departments"] = (
            Department.objects.prefetch_related(
                Prefetch("teams", queryset=teams_qs)
            ).order_by("name")
        )
        return ctx


class TeamTypeListView(LoginRequiredMixin, ListView):
    model = TeamType
    template_name = "organisation/team_type_list.html"
    context_object_name = "team_types"

    def get_queryset(self):
        return super().get_queryset().annotate(num_teams=Count("teams"))


class FocusAreaListView(LoginRequiredMixin, ListView):
    model = FocusArea
    template_name = "organisation/focus_area_list.html"
    context_object_name = "focus_areas"

    def get_queryset(self):
        return super().get_queryset().annotate(num_departments=Count("departments"))
