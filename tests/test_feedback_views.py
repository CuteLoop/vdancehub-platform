from datetime import UTC, datetime

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.feedback.models import FeedbackRequest


@pytest.fixture
def adult(db: None) -> User:
    return User.objects.create_user(
        email="adult@example.com",
        password="secret",
        display_name="Adult dancer",
        adult_confirmed_at=datetime.now(UTC),
    )


@pytest.mark.django_db
def test_home_exposes_all_six_product_activities(client: Client) -> None:
    response = client.get(reverse("home"))
    assert response.status_code == 200
    for label in (
        "Discuss",
        "Get Feedback",
        "Explore",
        "Find Mentors",
        "Collaborate",
        "Find Community",
    ):
        assert label in response.content.decode()


@pytest.mark.django_db
def test_adult_can_create_unlisted_feedback_request(client: Client, adult: User) -> None:
    client.force_login(adult)
    response = client.post(
        reverse("feedback:create"),
        {
            "video_url": "https://youtu.be/abc_DEF-12x?si=discard",
            "attribution_name": "Adult dancer",
            "video_description": "Basic-step timing practice.",
            "title": "Help with timing",
            "goals": "Stay on time during the full basic.",
            "dancer_role": "follower",
            "skill_level": "beginner",
            "footage_consent_confirmed": "on",
            "adults_only_confirmed": "on",
            "constructive_guidelines_accepted": "on",
        },
    )
    feedback_request = FeedbackRequest.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("feedback:detail", kwargs={"pk": feedback_request.pk})
    assert feedback_request.video.visibility == "unlisted"

    client.logout()
    detail = client.get(response.url)
    assert detail.status_code == 200
    assert "Anyone with the link" in detail.content.decode()


@pytest.mark.django_db
def test_account_without_adult_confirmation_cannot_open_creation_form(client: Client) -> None:
    user = User.objects.create_user(
        email="unknown-age@example.com", password="secret", display_name="Dancer"
    )
    client.force_login(user)
    response = client.get(reverse("feedback:create"))
    assert response.status_code == 403
