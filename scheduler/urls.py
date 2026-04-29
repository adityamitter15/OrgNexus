# File: scheduler/urls.py - Aditya Mitter (W19869650)

from django.urls import path

from . import views


app_name = "scheduler"


urlpatterns = [
    path("", views.UpcomingMeetingsView.as_view(), name="upcoming"),
    path("week/", views.WeeklyView.as_view(), name="week"),
    path("month/", views.MonthlyView.as_view(), name="month"),
    path("new/", views.MeetingCreateView.as_view(), name="create"),
    path("<int:pk>/", views.MeetingDetailView.as_view(), name="detail"),
    path("<int:pk>/respond/<str:response>/", views.respond, name="respond"),
]
