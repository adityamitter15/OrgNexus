# File: core/urls.py - Aditya Mitter (W19869650)

from django.urls import path

from . import views


app_name = "core"


urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("search/", views.search, name="search"),
]
