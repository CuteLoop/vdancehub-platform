from django.urls import path

from . import views

app_name = "knowledge"

urlpatterns = [
    path("curricula/", views.curriculum_list, name="curriculum-list"),
    path("curricula/<slug:slug>/", views.curriculum_detail, name="curriculum-detail"),
    path("graph/", views.graph, name="graph"),
    path("moves/", views.movement_list, name="movement-list"),
    path("moves/<slug:slug>/", views.movement_detail, name="movement-detail"),
]
