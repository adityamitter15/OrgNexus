# File: organisation/admin.py - Aditya Mitter (W19869650)

from django.contrib import admin

from .models import Department, DepartmentHead, FocusArea


@admin.register(FocusArea)
class FocusAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name", "description")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "specialisation", "focus_area", "created_at")
    list_filter = ("focus_area",)
    search_fields = ("name", "specialisation", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(DepartmentHead)
class DepartmentHeadAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "appointed", "stepped_down")
    list_filter = ("department",)
    autocomplete_fields = ("user", "department")
    search_fields = ("user__username", "user__full_name", "department__name")
