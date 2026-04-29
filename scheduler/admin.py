# File: scheduler/admin.py - Aditya Mitter (W19869650)

from django.contrib import admin

from .models import Meeting, MeetingParticipant


class MeetingParticipantInline(admin.TabularInline):
    model = MeetingParticipant
    extra = 1
    autocomplete_fields = ("user",)


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "date_time", "platform", "recurrence", "created_by")
    list_filter = ("recurrence", "platform")
    search_fields = ("title", "agenda", "created_by__username")
    autocomplete_fields = ("created_by",)
    inlines = [MeetingParticipantInline]


@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = ("meeting", "user", "status", "responded_at")
    list_filter = ("status",)
    autocomplete_fields = ("meeting", "user")
