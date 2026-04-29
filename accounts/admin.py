# File: accounts/admin.py - Aditya Mitter (W19869650)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class OrgNexusUserAdmin(UserAdmin):
    """Custom user admin - shows the OrgNexus profile fields next to
    Django's built-in ones."""

    fieldsets = UserAdmin.fieldsets + (
        ("OrgNexus profile", {"fields": ("full_name", "job_title", "avatar",
                                          "email_verified")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("OrgNexus profile", {"fields": ("email", "full_name", "job_title")}),
    )
    list_display = (
        "username",
        "full_name",
        "email",
        "job_title",
        "email_verified",
        "is_active",
        "is_staff",
    )
    list_filter = ("is_active", "is_staff", "email_verified")
    search_fields = ("username", "email", "full_name", "job_title")
    ordering = ("username",)
