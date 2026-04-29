# File: organisation/urls.py - Noah Gil De Matos Jimenez

from django.urls import path

from . import views


app_name = "organisation"


urlpatterns = [
    path("", views.DepartmentListView.as_view(), name="department_list"),
    path("structure/", views.OrgStructureView.as_view(), name="structure"),
    path("types/", views.TeamTypeListView.as_view(), name="team_type_list"),
    path("focus-areas/", views.FocusAreaListView.as_view(), name="focus_area_list"),
    path(
        "<slug:slug>/",
        views.DepartmentDetailView.as_view(),
        name="department_detail",
    ),
]
