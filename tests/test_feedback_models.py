import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.feedback.models import FeedbackRequest
from apps.mediarefs.models import VideoReference


@pytest.mark.django_db
def test_feedback_request_requires_owner_and_all_consent_assertions() -> None:
    owner = User.objects.create_user(
        email="owner@example.com", password="secret", display_name="Owner"
    )
    other = User.objects.create_user(
        email="other@example.com", password="secret", display_name="Other"
    )
    video = VideoReference.objects.create(
        owner=owner,
        submitted_url="https://youtu.be/abc_DEF-12x",
        attribution_name="Owner",
        description="Practice footage.",
    )
    base = {
        "video": video,
        "title": "Help with timing",
        "goals": "Understand timing through the basic step.",
        "dancer_role": FeedbackRequest.DancerRole.FOLLOWER,
        "skill_level": FeedbackRequest.SkillLevel.BEGINNER,
        "footage_consent_confirmed": True,
        "adults_only_confirmed": True,
        "constructive_guidelines_accepted": True,
    }
    with pytest.raises(ValidationError):
        FeedbackRequest.objects.create(author=other, **base)

    base["footage_consent_confirmed"] = False
    with pytest.raises(ValidationError):
        FeedbackRequest.objects.create(author=owner, **base)

    base["footage_consent_confirmed"] = True
    request = FeedbackRequest.objects.create(author=owner, **base)
    assert request.video == video
