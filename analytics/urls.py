# File: analytics/urls.py - Aditya Mitter (W19869650)

from django.urls import path

from . import views


app_name = "analytics"


urlpatterns = [
    path("", views.charts, name="charts"),
    path("data/teams-per-dept/", views.teams_per_dept_data, name="data_teams_per_dept"),
    path("data/projects-per-dept/", views.projects_per_dept_data, name="data_projects_per_dept"),
]
