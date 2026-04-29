# File: teams/admin.py - Aditya Mitter (W19869650)

from django.contrib import admin

from .models import (
    Skill,
    Staff,
    Team,
    TeamDependency,
    TeamLeader,
    TeamMembership,
    TeamSkill,
    TeamType,
)


@admin.register(TeamType)
class TeamTypeAdmin(admin.ModelAdmin):
    list_display = ("type_name", "description")
    search_fields = ("type_name", "description")


class StaffInline(admin.TabularInline):
    model = Staff
    extra = 1
    autocomplete_fields = ("user",)


class TeamSkillInline(admin.TabularInline):
    model = TeamSkill
    extra = 1
    autocomplete_fields = ("skill",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "team_type", "manager", "created_at")
    list_filter = ("department", "team_type")
    search_fields = ("name", "department__name", "manager__full_name", "slack_channel")
    autocomplete_fields = ("department", "manager", "team_type")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = [StaffInline, TeamSkillInline]


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "role", "is_active", "joined_on")
    list_filter = ("team", "is_active")
    autocomplete_fields = ("user", "team")
    search_fields = ("user__username", "user__full_name", "team__name")


@admin.register(TeamLeader)
class TeamLeaderAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "appointed", "stepped_down")
    list_filter = ("team",)
    autocomplete_fields = ("user", "team")


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "joined_at", "left_at")
    list_filter = ("team",)
    autocomplete_fields = ("user", "team")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(TeamSkill)
class TeamSkillAdmin(admin.ModelAdmin):
    list_display = ("team", "skill", "proficiency")
    list_filter = ("proficiency", "team")
    autocomplete_fields = ("team", "skill")


@admin.register(TeamDependency)
class TeamDependencyAdmin(admin.ModelAdmin):
    list_display = ("upstream", "downstream", "dependency_type", "created_at")
    list_filter = ("dependency_type",)
    autocomplete_fields = ("upstream", "downstream")
    search_fields = ("upstream__name", "downstream__name")
