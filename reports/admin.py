# File: reports/admin.py - Aditya Mitter (W19869650)

from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "lead", "status", "started_on")
    list_filter = ("status", "department")
    search_fields = ("name", "description", "department__name")
    autocomplete_fields = ("department", "lead")
