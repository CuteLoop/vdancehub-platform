from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from apps.core.views import home


def health(_: object) -> JsonResponse:
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("discussions/", include("apps.discussions.urls")),
    path("feedback/", include("apps.feedback.urls")),
    path("knowledge/", include("apps.knowledge.urls")),
    path("health/", health, name="health"),
]
