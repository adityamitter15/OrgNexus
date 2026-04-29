# File: orgnexus/urls.py - Aditya Mitter (W19869650)
"""Top-level URL router. Each app keeps its own urls.py so ownership
between team members is clear."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Brand the admin site - the brief points the marker at the Django
# admin so it's worth making it feel like part of OrgNexus.
admin.site.site_header = "OrgNexus Admin"
admin.site.site_title = "OrgNexus"
admin.site.index_title = "Sky Engineering Portal - admin"


urlpatterns = [
    path("admin/", admin.site.urls),

    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("teams/", include(("teams.urls", "teams"), namespace="teams")),
    path("organisation/", include(("organisation.urls", "organisation"), namespace="organisation")),
    path("messages/", include(("messaging.urls", "messaging"), namespace="messaging")),
    path("schedule/", include(("scheduler.urls", "scheduler"), namespace="scheduler")),
    path("reports/", include(("reports.urls", "reports"), namespace="reports")),
    path("analytics/", include(("analytics.urls", "analytics"), namespace="analytics")),
    path("", include(("core.urls", "core"), namespace="core")),
]

# In dev, serve uploaded avatars through Django so the demo doesn't
# need a separate web server.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
