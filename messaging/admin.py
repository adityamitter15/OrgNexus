# File: messaging/admin.py - Noah Gil De Matos Jimenez

from django.contrib import admin

from .models import Message, MessageRecipient


class MessageRecipientInline(admin.TabularInline):
    model = MessageRecipient
    extra = 1
    autocomplete_fields = ("recipient",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "sender", "status", "created_at", "sent_at")
    list_filter = ("status",)
    search_fields = ("subject", "body", "sender__username")
    autocomplete_fields = ("sender",)
    inlines = [MessageRecipientInline]
    readonly_fields = ("created_at", "sent_at")


@admin.register(MessageRecipient)
class MessageRecipientAdmin(admin.ModelAdmin):
    list_display = ("message", "recipient", "is_read", "read_at")
    list_filter = ("is_read",)
    autocomplete_fields = ("message", "recipient")
