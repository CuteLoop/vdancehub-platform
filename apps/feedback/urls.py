from django.urls import path

from . import views

app_name = "feedback"

urlpatterns = [
    path("new/", views.create_feedback_request, name="create"),
    path("<uuid:pk>/", views.feedback_request_detail, name="detail"),
]
