from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.mentoring.models import (
    Enrollment,
    InstructorProfile,
    InstructorReview,
    PracticeAssignment,
    PracticeSubmission,
    PracticeTemplate,
    ReviewAnnotation,
)


def adult_user(email: str, display_name: str) -> User:
    return User.objects.create_user(
        email=email,
        password="secret",
        display_name=display_name,
        adult_confirmed_at=timezone.now(),
    )


@pytest.mark.django_db
def test_instructor_can_publish_profile_and_create_reusable_practice(client) -> None:
    instructor = adult_user("teacher@example.com", "Teacher")
    client.force_login(instructor)

    profile_response = client.post(
        reverse("mentoring:become"),
        {
            "professional_name": "Teacher Ana",
            "slug": "teacher-ana",
            "biography": "Bachata and Salsa instructor focused on social dancing.",
            "languages": "English, Spanish",
            "remote_available": True,
            "is_published": True,
        },
    )
    assert profile_response.status_code == 302

    template_response = client.post(
        reverse("mentoring:template-create"),
        {
            "title": "Bachata Weight Transfer",
            "objective": "Develop clear weight transfer and rhythmic consistency.",
            "instructions": "Practice without music, then repeat with a slow song.",
            "evaluation_criteria": "Timing, balance, weight transfer, continuity",
            "estimated_minutes": 15,
            "is_public": True,
        },
    )
    assert template_response.status_code == 302
    assert PracticeTemplate.objects.get().instructor.user == instructor

    directory = client.get(reverse("mentoring:directory"))
    assert b"Teacher Ana" in directory.content
    assert b"Bachata Weight Transfer" in directory.content


@pytest.mark.django_db
def test_private_assignment_submission_review_and_history_workflow(client) -> None:
    instructor_user = adult_user("mentor@example.com", "Mentor")
    student = adult_user("student@example.com", "Student")
    stranger = adult_user("stranger@example.com", "Stranger")
    instructor = InstructorProfile.objects.create(
        user=instructor_user,
        professional_name="Mentor Mia",
        slug="mentor-mia",
        biography="Technique mentor.",
        languages=["English"],
        is_published=True,
    )
    template = PracticeTemplate.objects.create(
        instructor=instructor,
        title="Week 3 — Weight Transfer",
        objective="Complete each transfer before the next step.",
        instructions="Practice for fifteen minutes and submit a short clip.",
        evaluation_criteria="Timing, balance, continuity",
        estimated_minutes=15,
    )

    client.force_login(instructor_user)
    assignment_response = client.post(
        reverse("mentoring:assignment-create"),
        {
            "student_email": student.email,
            "template": str(template.pk),
            "due_at": (timezone.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M"),
            "personalized_notes": "Focus on the end of each transfer.",
        },
    )
    assert assignment_response.status_code == 302
    assignment = PracticeAssignment.objects.get()
    assert assignment.enrollment.student == student
    assert assignment.enrollment.status == Enrollment.Status.ACTIVE

    client.force_login(stranger)
    stranger_detail = client.get(reverse("mentoring:assignment-detail", args=[assignment.pk]))
    assert stranger_detail.status_code == 404

    client.force_login(student)
    dashboard = client.get(reverse("mentoring:student-dashboard"))
    assert b"Week 3" in dashboard.content
    assert dashboard.headers["X-Robots-Tag"] == "noindex, nofollow"
    assert dashboard.headers["Cache-Control"] == "private, no-store"
    submission_response = client.post(
        reverse("mentoring:submit", args=[assignment.pk]),
        {
            "video_url": "https://youtu.be/abc_DEF-12x?t=23",
            "video_description": "Front view of this week's practice.",
            "self_assessment": "Timing felt steadier; the right side is still less balanced.",
        },
    )
    assert submission_response.status_code == 302
    submission = PracticeSubmission.objects.get()
    assert submission.video.visibility == "unlisted"

    client.force_login(instructor_user)
    studio = client.get(reverse("mentoring:studio"))
    assert b"1" in studio.content
    assert b"Timing felt steadier" in studio.content
    review_response = client.post(
        reverse("mentoring:review", args=[submission.pk]),
        {
            "overall_feedback": "Good improvement in rhythmic consistency.",
            "next_steps": "Finish the transfer before stepping again.",
            "annotations": "23|timing|Complete the transfer before the next step.",
        },
    )
    assert review_response.status_code == 302
    assert InstructorReview.objects.count() == 1
    assert ReviewAnnotation.objects.get().seconds == 23

    client.force_login(student)
    history = client.get(reverse("mentoring:assignment-detail", args=[assignment.pk]))
    assert history.status_code == 200
    assert b"Good improvement" in history.content
    assert b"00:23" in history.content


@pytest.mark.django_db
def test_instructor_cannot_access_another_mentor_private_submission(client) -> None:
    mentor_a_user = adult_user("a@example.com", "Mentor A")
    mentor_b_user = adult_user("b@example.com", "Mentor B")
    student = adult_user("private-student@example.com", "Private Student")
    mentor_a = InstructorProfile.objects.create(
        user=mentor_a_user,
        professional_name="Mentor A",
        slug="mentor-a",
        biography="A",
        languages=["English"],
    )
    InstructorProfile.objects.create(
        user=mentor_b_user,
        professional_name="Mentor B",
        slug="mentor-b",
        biography="B",
        languages=["English"],
    )
    enrollment = Enrollment.objects.create(
        instructor=mentor_a, student=student, status=Enrollment.Status.ACTIVE
    )
    template = PracticeTemplate.objects.create(
        instructor=mentor_a,
        title="Private practice",
        objective="Private",
        instructions="Private",
        evaluation_criteria="Private",
        estimated_minutes=10,
    )
    assignment = PracticeAssignment.objects.create(enrollment=enrollment, template=template)

    client.force_login(mentor_b_user)
    private_detail = client.get(reverse("mentoring:assignment-detail", args=[assignment.pk]))
    assert private_detail.status_code == 404
