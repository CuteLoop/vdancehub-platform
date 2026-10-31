import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.mediarefs.models import VideoReference


@pytest.fixture
def owner(db: None) -> User:
    return User.objects.create_user(
        email="dancer@example.com", password="secret", display_name="Dancer"
    )


@pytest.mark.django_db
def test_email_login_user_receives_a_unique_pseudonymous_forum_handle() -> None:
    first = User.objects.create_user(
        email="first@example.com", password="secret", display_name="Dancer"
    )
    second = User.objects.create_user(
        email="second@example.com", password="secret", display_name="Dancer"
    )
    assert first.username.startswith("member-")
    assert first.username != second.username


@pytest.mark.django_db
def test_video_reference_is_unlisted_and_canonicalized_by_default(owner: User) -> None:
    reference = VideoReference.objects.create(
        owner=owner,
        submitted_url="https://youtu.be/abc_DEF-12x?si=discarded",
        attribution_name="Original creator",
        description="Practice footage for timing feedback.",
    )
    assert reference.visibility == VideoReference.Visibility.UNLISTED
    assert reference.canonical_url == "https://www.youtube.com/watch?v=abc_DEF-12x"
    assert reference.embed_url == "https://www.youtube-nocookie.com/embed/abc_DEF-12x"
    assert reference.can_view(owner)
    assert not reference.can_view(None)
    assert reference.can_view(None, via_direct_link=True)
    assert not reference.is_discoverable


@pytest.mark.django_db
def test_public_promotion_is_explicit(owner: User) -> None:
    reference = VideoReference.objects.create(
        owner=owner,
        submitted_url="https://www.instagram.com/reel/ABC_def12/",
        attribution_name="Original creator",
        description="Footwork reference.",
    )
    assert reference.embed_url is None
    reference.promote_public()
    assert reference.visibility == VideoReference.Visibility.PUBLIC
    assert reference.promoted_at is not None
    assert reference.can_view(None)
    assert reference.is_discoverable


@pytest.mark.django_db
def test_duplicate_video_for_same_owner_is_rejected(owner: User) -> None:
    fields = {
        "owner": owner,
        "submitted_url": "https://youtu.be/abc_DEF-12x",
        "attribution_name": "Original creator",
        "description": "Practice footage.",
    }
    VideoReference.objects.create(**fields)
    with pytest.raises(ValidationError):
        VideoReference.objects.create(**fields)


@pytest.mark.django_db
def test_withdrawn_reference_is_not_viewable_or_promotable(owner: User) -> None:
    from django.utils import timezone

    reference = VideoReference.objects.create(
        owner=owner,
        submitted_url="https://youtu.be/abc_DEF-12x",
        attribution_name="Original creator",
        description="Practice footage.",
        withdrawn_at=timezone.now(),
    )
    assert not reference.can_view(owner)
    with pytest.raises(ValidationError):
        reference.promote_public()
