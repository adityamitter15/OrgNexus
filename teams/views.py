# File: teams/views.py - Aditya Mitter (W19869650)
"""Team menu - my (Aditya's) main individual element.

Maps to the brief's group-of-N split, slot 1: Team display, search,
contact, schedule meeting (entry-points to other apps), skills,
dependencies up/down.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import TeamDependencyForm, TeamForm
from .models import Team


class TeamListView(LoginRequiredMixin, ListView):
    """Team menu landing page. Search box hits ?q=… and filters by name,
    department, manager or Slack channel."""

    model = Team
    template_name = "teams/team_list.html"
    context_object_name = "teams"
    paginate_by = 12

    def get_queryset(self):
        # select_related avoids N+1 queries when the list template
        # touches dept / manager / team_type for every row.
        qs = (
            super()
            .get_queryset()
            .select_related("department", "team_type", "manager")
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(department__name__icontains=q)
                | Q(manager__full_name__icontains=q)
                | Q(slack_channel__icontains=q)
            )

        # Optional dept filter from a dropdown on the list page.
        dept = self.request.GET.get("department")
        if dept:
            qs = qs.filter(department__slug=dept)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["selected_dept"] = self.request.GET.get("department", "")
        # The dept filter dropdown needs its options.
        from organisation.models import Department
        ctx["departments"] = Department.objects.order_by("name")
        return ctx


class TeamDetailView(LoginRequiredMixin, DetailView):
    """Hits every CW1 'view *' use case in one page: mission, manager,
    contact channels, members, code repos, dependencies up + down."""

    model = Team
    template_name = "teams/team_detail.html"
    context_object_name = "team"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("department", "team_type", "manager")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        team = ctx["team"]
        ctx["upstream"] = (
            team.upstream_links.select_related("upstream").all()
        )
        ctx["downstream"] = (
            team.downstream_links.select_related("downstream").all()
        )
        ctx["members"] = (
            team.staff.select_related("user").filter(is_active=True)
        )
        ctx["leaders"] = (
            team.leaders.select_related("user").filter(stepped_down__isnull=True)
        )
        ctx["skills"] = team.team_skills.select_related("skill").all()
        return ctx


class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = "teams/team_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"Team \"{form.instance.name}\" created.")
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url() if hasattr(self.object, "get_absolute_url") \
            else reverse_lazy("teams:detail", args=[self.object.slug])


class TeamUpdateView(LoginRequiredMixin, UpdateView):
    model = Team
    form_class = TeamForm
    template_name = "teams/team_form.html"
    slug_field = "slug"

    def form_valid(self, form):
        messages.success(self.request, "Team updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("teams:detail", args=[self.object.slug])


class TeamDeleteView(LoginRequiredMixin, DeleteView):
    model = Team
    template_name = "teams/team_confirm_delete.html"
    slug_field = "slug"
    success_url = reverse_lazy("teams:list")

    def form_valid(self, form):
        messages.warning(self.request, f"Team \"{self.object.name}\" deleted.")
        return super().form_valid(form)


class TeamDependenciesView(LoginRequiredMixin, DetailView):
    """Standalone page for the upstream/downstream graph.

    Detail view linked to it too, but the brief asks for a dedicated
    'View Dependencies (Up/Down)' use case so we expose this URL.
    """

    model = Team
    template_name = "teams/team_dependencies.html"
    context_object_name = "team"
    slug_field = "slug"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        team = ctx["team"]
        ctx["upstream"] = team.upstream_links.select_related("upstream").all()
        ctx["downstream"] = team.downstream_links.select_related("downstream").all()
        return ctx


class DependencyCreateView(LoginRequiredMixin, CreateView):
    form_class = TeamDependencyForm
    template_name = "teams/dependency_form.html"

    def get_initial(self):
        slug = self.kwargs.get("slug")
        team = get_object_or_404(Team, slug=slug)
        # Pre-fill 'upstream' to the current team so the user doesn't
        # have to re-pick it from a long dropdown.
        return {"upstream": team}

    def form_valid(self, form):
        messages.success(self.request, "Dependency added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("teams:dependencies", args=[self.kwargs["slug"]])
