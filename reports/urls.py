# File: reports/urls.py - Aditya Mitter (W19869650)

from django.urls import path

from . import views


app_name = "reports"


urlpatterns = [
    path("", views.report_index, name="index"),
    path("pdf/", views.pdf_report, name="pdf"),
    path("xlsx/", views.xlsx_report, name="xlsx"),
    path("teams-without-managers/", views.teams_without_managers, name="orphans"),
    path("departments-without-heads/", views.departments_without_heads, name="dept_orphans"),
]
