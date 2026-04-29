# File: messaging/views.py - Noah Gil De Matos Jimenez (Aditya integrated nav links)
"""Inbox / Sent / Drafts and message create flow."""

from django.contrib import messages as flash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView

from .forms import MessageForm
from .models import Message, MessageRecipient


class InboxView(LoginRequiredMixin, ListView):
    template_name = "messaging/inbox.html"
    context_object_name = "rows"
    paginate_by = 20

    def get_queryset(self):
        return (
            MessageRecipient.objects
            .filter(recipient=self.request.user, message__status=Message.SENT)
            .select_related("message", "message__sender")
            .order_by("-message__sent_at")
        )


class SentView(LoginRequiredMixin, ListView):
    template_name = "messaging/sent.html"
    context_object_name = "messages_list"
    paginate_by = 20

    def get_queryset(self):
        return (
            Message.objects
            .filter(sender=self.request.user, status=Message.SENT)
            .order_by("-sent_at")
        )


class DraftsView(LoginRequiredMixin, ListView):
    template_name = "messaging/drafts.html"
    context_object_name = "messages_list"
    paginate_by = 20

    def get_queryset(self):
        return (
            Message.objects
            .filter(sender=self.request.user, status=Message.DRAFT)
            .order_by("-created_at")
        )


class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = "messaging/message_detail.html"
    context_object_name = "message"

    def get_object(self, queryset=None):
        # Only the sender or any recipient should be able to read the
        # body - we filter at the queryset level.
        msg = get_object_or_404(Message, pk=self.kwargs["pk"])
        is_sender = msg.sender_id == self.request.user.id
        is_recipient = msg.recipients.filter(recipient=self.request.user).exists()
        if not (is_sender or is_recipient):
            from django.http import Http404
            raise Http404("Message not found.")
        # Mark-as-read on first fetch by the recipient.
        if is_recipient:
            (
                MessageRecipient.objects
                .filter(message=msg, recipient=self.request.user, is_read=False)
                .update(is_read=True, read_at=timezone.now())
            )
        return msg


class MessageCreateView(LoginRequiredMixin, CreateView):
    form_class = MessageForm
    template_name = "messaging/message_form.html"

    def form_valid(self, form):
        msg = form.save(commit=False)
        msg.sender = self.request.user
        # Decide draft vs send by which submit button was hit.
        action = self.request.POST.get("action", "send")
        if action == "draft":
            msg.status = Message.DRAFT
        else:
            msg.status = Message.SENT
            msg.sent_at = timezone.now()
        msg.save()

        for user in form.cleaned_data["recipients"]:
            MessageRecipient.objects.create(message=msg, recipient=user)

        flash.success(
            self.request,
            "Saved as draft." if msg.is_sent is False else "Message sent.",
        )
        if msg.status == Message.DRAFT:
            return redirect("messaging:drafts")
        return redirect("messaging:sent")


@login_required
def send_draft(request, pk):
    """Promote a draft to sent and stamp sent_at."""
    msg = get_object_or_404(Message, pk=pk, sender=request.user, status=Message.DRAFT)
    msg.status = Message.SENT
    msg.sent_at = timezone.now()
    msg.save(update_fields=["status", "sent_at"])
    flash.success(request, "Message sent.")
    return redirect("messaging:sent")


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = "messaging/message_confirm_delete.html"
    success_url = reverse_lazy("messaging:inbox")

    def get_queryset(self):
        # Only the sender can delete (recipients can ignore).
        return Message.objects.filter(sender=self.request.user)
