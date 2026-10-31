import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import User
from apps.mentoring.models import ExternalLink


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    [
        "http://booking.example/lesson",
        "https://user:pass@booking.example/lesson",
        "https://booking.example:443/lesson",
        "https://localhost/lesson",
        "https://127.0.0.1/lesson",
        "https://10.0.0.1/lesson",
    ],
)
def test_external_booking_link_rejects_unsafe_destinations(url: str) -> None:
    owner = User.objects.create_user(
        email=f"owner-{abs(hash(url))}@example.com", password="secret", display_name="Teacher"
    )
    with pytest.raises(ValidationError):
        ExternalLink.objects.create(owner=owner, url=url, label="Book")


@pytest.mark.django_db
def test_only_staff_can_approve_external_link() -> None:
    owner = User.objects.create_user(
        email="teacher@example.com", password="secret", display_name="Teacher"
    )
    moderator = User.objects.create_user(
        email="moderator@example.com",
        password="secret",
        display_name="Moderator",
        is_staff=True,
    )
    link = ExternalLink.objects.create(
        owner=owner, url="https://booking.example/lesson", label="Book a lesson"
    )
    with pytest.raises(PermissionDenied):
        link.approve(moderator=owner)
    link.approve(moderator=moderator)
    assert link.status == ExternalLink.ReviewStatus.APPROVED
    assert link.reviewed_by == moderator
    assert link.reviewed_at is not None
