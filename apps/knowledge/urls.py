from django.urls import path

from . import views

app_name = "knowledge"

urlpatterns = [
    path("moves/", views.movement_list, name="movement-list"),
    path("moves/<slug:slug>/", views.movement_detail, name="movement-detail"),
]
