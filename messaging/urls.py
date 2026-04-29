# File: messaging/urls.py - Noah Gil De Matos Jimenez

from django.urls import path

from . import views


app_name = "messaging"


urlpatterns = [
    path("", views.InboxView.as_view(), name="inbox"),
    path("inbox/", views.InboxView.as_view(), name="inbox_alt"),
    path("sent/", views.SentView.as_view(), name="sent"),
    path("drafts/", views.DraftsView.as_view(), name="drafts"),
    path("new/", views.MessageCreateView.as_view(), name="create"),
    path("<int:pk>/", views.MessageDetailView.as_view(), name="detail"),
    path("<int:pk>/send/", views.send_draft, name="send_draft"),
    path("<int:pk>/delete/", views.MessageDeleteView.as_view(), name="delete"),
]
