from django.urls import path

from . import views

app_name = "knowledge"

urlpatterns = [
    path("curricula/", views.curriculum_list, name="curriculum-list"),
    path("curricula/<slug:slug>/", views.curriculum_detail, name="curriculum-detail"),
    path(
        "curricula/<slug:slug>/discussion/",
        views.curriculum_discussion,
        name="curriculum-discussion",
    ),
    path(
        "curricula/<slug:slug>/discussion/reply/",
        views.reply_to_curriculum_discussion,
        name="curriculum-reply",
    ),
    path("pages/<slug:slug>/", views.page_detail, name="page-detail"),
    path(
        "pages/<slug:slug>/editions/<int:edition_number>/",
        views.edition_detail,
        name="edition-detail",
    ),
    path("graph/", views.graph, name="graph"),
    path("moves/", views.movement_list, name="movement-list"),
    path("moves/<slug:slug>/", views.movement_detail, name="movement-detail"),
]
