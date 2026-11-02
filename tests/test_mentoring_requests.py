from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.mentoring.models import (
    ExternalLink,
    InstructorProfile,
    MentoringOffer,
    MentoringRequest,
    PracticeAssignment,
    PracticeTemplate,
)


def adult_user(email: str, display_name: str, *, is_staff: bool = False) -> User:
    return User.objects.create_user(
        email=email,
        password="secret",
        display_name=display_name,
        adult_confirmed_at=timezone.now(),
        is_staff=is_staff,
    )


def mentor(user: User, slug: str) -> InstructorProfile:
    return InstructorProfile.objects.create(
        user=user,
        professional_name=user.display_name,
        slug=slug,
        biography="Social dance mentor.",
        languages=["English"],
        is_published=True,
    )


@pytest.mark.django_db
def test_instructor_creates_offer_but_booking_link_waits_for_staff_review(client) -> None:
    instructor_user = adult_user("offers@example.com", "Teacher Offers")
    profile = mentor(instructor_user, "teacher-offers")
    client.force_login(instructor_user)

    response = client.post(
        reverse("mentoring:offer-create"),
        {
            "title": "One-time bachata review",
            "description": "Focused feedback on one short practice video.",
            "format": MentoringOffer.Format.VIDEO_REVIEW,
            "price_amount": "35.00",
            "price_currency": "USD",
            "included_reviews": 1,
            "turnaround_days": 4,
            "terms": "Submit one video up to two minutes.",
            "booking_url": "https://booking.example/review",
            "booking_label": "Book a review",
        },
    )
    assert response.status_code == 302
    offer = MentoringOffer.objects.get(instructor=profile)
    assert offer.booking_link.status == ExternalLink.ReviewStatus.PENDING

    public_profile = client.get(reverse("mentoring:profile", args=[profile.slug]))
    assert b"One-time bachata review" in public_profile.content
    assert b'href="https://booking.example/review"' not in public_profile.content

    moderator = adult_user("moderator-offers@example.com", "Moderator", is_staff=True)
    offer.booking_link.approve(moderator=moderator)
    public_profile = client.get(reverse("mentoring:profile", args=[profile.slug]))
    assert b'href="https://booking.example/review"' in public_profile.content


@pytest.mark.django_db
def test_student_requests_one_time_review_and_instructor_accepts_into_assignment(client) -> None:
    instructor_user = adult_user("request-mentor@example.com", "Mentor Rosa")
    student = adult_user("request-student@example.com", "Dancer Kai")
    other_mentor_user = adult_user("other-mentor@example.com", "Other Mentor")
    instructor = mentor(instructor_user, "mentor-rosa")
    mentor(other_mentor_user, "other-mentor")
    link = ExternalLink.objects.create(
        owner=instructor_user,
        url="https://booking.example/rosa-review",
        label="Book review",
    )
    offer = MentoringOffer.objects.create(
        instructor=instructor,
        title="One-time salsa review",
        description="One focused review.",
        format=MentoringOffer.Format.VIDEO_REVIEW,
        price_amount="40.00",
        price_currency="USD",
        booking_link=link,
    )
    practice = PracticeTemplate.objects.create(
        instructor=instructor,
        title="Salsa video review",
        objective="Identify one strength and one next step.",
        instructions="Share a short clip and describe what you want help with.",
        evaluation_criteria="Timing, connection, clarity",
        estimated_minutes=10,
    )

    client.force_login(student)
    request_response = client.post(
        reverse("mentoring:request-review", args=[instructor.slug]),
        {
            "offer": str(offer.pk),
            "focus": "I want help with the timing of my cross-body lead.",
        },
    )
    assert request_response.status_code == 302
    mentoring_request = MentoringRequest.objects.get()
    assert mentoring_request.student == student
    assert mentoring_request.status == MentoringRequest.Status.REQUESTED

    duplicate_response = client.post(
        reverse("mentoring:request-review", args=[instructor.slug]),
        {
            "offer": str(offer.pk),
            "focus": "A duplicate request should not be created.",
        },
    )
    assert duplicate_response.status_code == 200
    assert MentoringRequest.objects.count() == 1

    client.force_login(other_mentor_user)
    unauthorized = client.get(reverse("mentoring:request-accept", args=[mentoring_request.pk]))
    assert unauthorized.status_code == 404

    client.force_login(instructor_user)
    studio = client.get(reverse("mentoring:studio"))
    assert b"I want help with the timing" in studio.content
    accept_response = client.post(
        reverse("mentoring:request-accept", args=[mentoring_request.pk]),
        {
            "template": str(practice.pk),
            "due_at": (timezone.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M"),
            "instructor_note": "Please send a 30–60 second social-dancing clip.",
        },
    )
    assert accept_response.status_code == 302
    mentoring_request.refresh_from_db()
    assert mentoring_request.status == MentoringRequest.Status.ACCEPTED
    assert mentoring_request.assignment is not None
    assert PracticeAssignment.objects.get().enrollment.student == student

    client.force_login(student)
    dashboard = client.get(reverse("mentoring:student-dashboard"))
    assert b"Salsa video review" in dashboard.content
    assert b"Accepted" in dashboard.content


@pytest.mark.django_db
def test_personal_practice_journal_is_visible_only_to_its_student(client) -> None:
    student = adult_user("journal@example.com", "Journal Dancer")
    stranger = adult_user("journal-stranger@example.com", "Stranger")
    client.force_login(student)
    response = client.post(
        reverse("mentoring:journal-create"),
        {
            "practice_date": timezone.localdate().isoformat(),
            "minutes": 25,
            "notes": "Worked on keeping my salsa basic compact and relaxed.",
            "video_url": "",
            "video_description": "",
        },
    )
    assert response.status_code == 302

    dashboard = client.get(reverse("mentoring:student-dashboard"))
    assert b"keeping my salsa basic compact" in dashboard.content

    client.force_login(stranger)
    stranger_dashboard = client.get(reverse("mentoring:student-dashboard"))
    assert b"keeping my salsa basic compact" not in stranger_dashboard.content
