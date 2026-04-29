# File: scheduler/views.py - Aditya Mitter (W19869650)
"""Schedule menu - meeting CRUD plus weekly/monthly/upcoming views."""

from datetime import timedelta

from django.contrib import messages as flash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from .forms import MeetingForm
from .models import Meeting, MeetingParticipant


def _my_meetings(user):
    """Meetings I either created or am invited to."""
    return Meeting.objects.filter(
        Q(created_by=user) | Q(participants__user=user)
    ).distinct()


class UpcomingMeetingsView(LoginRequiredMixin, ListView):
    template_name = "scheduler/upcoming.html"
    context_object_name = "meetings"
    paginate_by = 20

    def get_queryset(self):
        now = timezone.now()
        return _my_meetings(self.request.user).filter(date_time__gte=now).order_by("date_time")


class WeeklyView(LoginRequiredMixin, TemplateView):
    template_name = "scheduler/calendar_week.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.localtime()
        # ISO week: Monday as start.
        start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = start + timedelta(days=7)
        ctx["start"] = start
        ctx["end"] = end
        ctx["meetings"] = (
            _my_meetings(self.request.user)
            .filter(date_time__gte=start, date_time__lt=end)
            .order_by("date_time")
        )
        ctx["days"] = [start + timedelta(days=i) for i in range(7)]
        return ctx


class MonthlyView(LoginRequiredMixin, TemplateView):
    template_name = "scheduler/calendar_month.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.localtime()
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # rough month-end calc - jump to day 28 then forward 4 days.
        next_month = (start + timedelta(days=32)).replace(day=1)
        ctx["start"] = start
        ctx["end"] = next_month
        ctx["meetings"] = (
            _my_meetings(self.request.user)
            .filter(date_time__gte=start, date_time__lt=next_month)
            .order_by("date_time")
        )
        return ctx


class MeetingDetailView(LoginRequiredMixin, DetailView):
    model = Meeting
    template_name = "scheduler/meeting_detail.html"
    context_object_name = "meeting"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["participants"] = (
            ctx["meeting"].participants.select_related("user").all()
        )
        ctx["is_creator"] = ctx["meeting"].created_by_id == self.request.user.id
        ctx["my_invite"] = ctx["meeting"].participants.filter(
            user=self.request.user
        ).first()
        return ctx


class MeetingCreateView(LoginRequiredMixin, CreateView):
    form_class = MeetingForm
    template_name = "scheduler/meeting_form.html"
    success_url = reverse_lazy("scheduler:upcoming")

    def form_valid(self, form):
        meeting = form.save(commit=False)
        meeting.created_by = self.request.user
        meeting.save()

        # Always invite the creator so the meeting shows up in their
        # 'my meetings' list.
        MeetingParticipant.objects.get_or_create(
            meeting=meeting, user=self.request.user,
            defaults={"status": MeetingParticipant.ACCEPTED},
        )
        for user in form.cleaned_data.get("invitees", []):
            if user.id == self.request.user.id:
                continue
            MeetingParticipant.objects.get_or_create(meeting=meeting, user=user)

        flash.success(self.request, "Meeting scheduled.")
        return redirect("scheduler:detail", pk=meeting.pk)


@login_required
def respond(request, pk, response):
    """Accept or decline a meeting invite."""
    invite = get_object_or_404(MeetingParticipant, meeting_id=pk, user=request.user)
    response = response.upper()
    if response not in {MeetingParticipant.ACCEPTED, MeetingParticipant.DECLINED}:
        flash.error(request, "Unknown response.")
        return redirect("scheduler:detail", pk=pk)
    invite.status = response
    invite.responded_at = timezone.now()
    invite.save(update_fields=["status", "responded_at"])
    flash.success(request, f"Marked as {response.lower()}.")
    return redirect("scheduler:detail", pk=pk)
