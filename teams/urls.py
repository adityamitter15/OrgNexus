# File: teams/urls.py - Aditya Mitter (W19869650)

from django.urls import path

from . import views


app_name = "teams"


urlpatterns = [
    path("", views.TeamListView.as_view(), name="list"),
    path("new/", views.TeamCreateView.as_view(), name="create"),
    path("<slug:slug>/", views.TeamDetailView.as_view(), name="detail"),
    path("<slug:slug>/edit/", views.TeamUpdateView.as_view(), name="edit"),
    path("<slug:slug>/delete/", views.TeamDeleteView.as_view(), name="delete"),
    path(
        "<slug:slug>/dependencies/",
        views.TeamDependenciesView.as_view(),
        name="dependencies",
    ),
    path(
        "dependencies/new/<slug:slug>/",
        views.DependencyCreateView.as_view(),
        name="dependency_create",
    ),
]
