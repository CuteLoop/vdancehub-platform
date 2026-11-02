from django.urls import path

from . import views

app_name = "mentoring"

urlpatterns = [
    path("", views.mentor_directory, name="directory"),
    path("become-a-mentor/", views.become_a_mentor, name="become"),
    path("mentors/<slug:slug>/", views.mentor_profile, name="profile"),
    path("mentors/<slug:slug>/request-review/", views.request_review, name="request-review"),
    path("studio/", views.instructor_studio, name="studio"),
    path("studio/offers/new/", views.create_offer, name="offer-create"),
    path("studio/practice/new/", views.create_practice_template, name="template-create"),
    path("studio/assignments/new/", views.create_assignment, name="assignment-create"),
    path(
        "studio/requests/<uuid:pk>/accept/",
        views.accept_request,
        name="request-accept",
    ),
    path("studio/submissions/<uuid:pk>/review/", views.review_submission, name="review"),
    path("my-training/", views.student_dashboard, name="student-dashboard"),
    path("my-training/journal/new/", views.create_journal_entry, name="journal-create"),
    path("assignments/<uuid:pk>/", views.assignment_detail, name="assignment-detail"),
    path("assignments/<uuid:pk>/submit/", views.submit_practice, name="submit"),
]
