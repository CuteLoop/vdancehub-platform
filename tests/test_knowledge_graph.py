import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.discussions.models import DiscussionTopic
from apps.discussions.services import create_topic_with_first_post
from apps.knowledge.models import Movement, MovementRelationship, SourceReference
from apps.taxonomy.models import DanceStyle


@pytest.mark.parametrize(
    ("url", "provider", "canonical", "status"),
    [
        (
            "https://www.instagram.com/reel/ABC_def12/?utm_source=share",
            "instagram",
            "https://www.instagram.com/reel/ABC_def12/",
            "domain_validated",
        ),
        (
            "https://youtu.be/abc_DEF-12x?si=tracking&t=45",
            "youtube",
            "https://www.youtube.com/watch?v=abc_DEF-12x",
            "domain_validated",
        ),
        (
            "https://bachatasteps.com/?utm_source=reddit",
            "website",
            "https://bachatasteps.com/",
            "domain_validated",
        ),
        (
            "https://example.org/lesson?utm_source=test&part=2#notes",
            "website",
            "https://example.org/lesson?part=2",
            "unreviewed",
        ),
    ],
)
@pytest.mark.django_db
def test_source_reference_canonicalizes_and_classifies_urls(
    url: str, provider: str, canonical: str, status: str
) -> None:
    owner = User.objects.create_user(email="owner@example.com", display_name="Owner")
    reference = SourceReference.objects.create(
        submitted_url=url,
        title="Source",
        attribution_name="Creator",
        added_by=owner,
    )

    assert reference.provider == provider
    assert reference.canonical_url == canonical
    assert reference.validation_status == status
    assert reference.is_clickable is (status == "domain_validated")


@pytest.mark.parametrize(
    "url",
    [
        "http://instagram.com/reel/ABC_def12/",
        "https://instagram.com.evil.example/reel/ABC_def12/",
        "https://instagram.com@evil.example/reel/ABC_def12/",
        "https://user:pass@instagram.com/reel/ABC_def12/",
        "https://instagram.com:443/reel/ABC_def12/",
        "javascript:alert(1)",
        "https://127.0.0.1/reference",
    ],
)
@pytest.mark.django_db
def test_source_reference_rejects_unsafe_destinations(url: str) -> None:
    owner = User.objects.create_user(email="owner@example.com", display_name="Owner")
    with pytest.raises(ValidationError):
        SourceReference.objects.create(
            submitted_url=url,
            title="Unsafe",
            attribution_name="Unknown",
            added_by=owner,
        )


@pytest.mark.django_db
def test_knowledge_directory_and_movement_graph_are_discoverable(client) -> None:
    owner = User.objects.create_user(email="owner@example.com", display_name="Owner")
    bachata = DanceStyle.objects.create(name="Bachata", slug="bachata")
    basic = Movement.objects.create(
        name="Basic Footwork",
        slug="basic-footwork",
        dance_style=bachata,
        summary="A foundational movement concept.",
        is_concept=True,
        created_by=owner,
    )
    mambo = Movement.objects.create(
        name="Mambo Side-to-Side",
        slug="mambo-side-to-side",
        dance_style=bachata,
        summary="Catalog movement.",
        difficulty=1,
        source_catalog="BachataSteps",
        source_identifier="1590",
        created_by=owner,
    )
    MovementRelationship.objects.create(
        from_movement=mambo,
        to_movement=basic,
        kind=MovementRelationship.Kind.PREREQUISITE,
        status=MovementRelationship.Status.PROPOSED,
        provenance=MovementRelationship.Provenance.INFERRED,
        created_by=owner,
    )

    directory = client.get(reverse("knowledge:movement-list"), {"difficulty": "1"})
    assert directory.status_code == 200
    assert b"Mambo Side-to-Side" in directory.content
    assert b"Basic Footwork" not in directory.content

    detail = client.get(reverse("knowledge:movement-detail", args=[mambo.slug]))
    assert detail.status_code == 200
    assert b"Basic Footwork" in detail.content
    assert b"Proposed" in detail.content


@pytest.mark.django_db
def test_discussion_reply_creates_numbered_safe_references(client) -> None:
    author = User.objects.create_user(email="author@example.com", display_name="Author")
    author.adult_confirmed_at = timezone.now()
    author.save(update_fields=["adult_confirmed_at"])
    thread = create_topic_with_first_post(
        author=author,
        title="Body wave terminology",
        kind=DiscussionTopic.Kind.DISCUSSION,
        body="What terminology do you use?",
    )
    topic = thread.native_topic
    assert topic is not None
    assert client.login(email=author.email, password=None) is False
    author.set_password("secret")
    author.save(update_fields=["password"])
    assert client.login(email=author.email, password="secret")

    response = client.post(
        reverse("discussions:reply", args=[topic.pk]),
        {
            "body": "This teacher demonstrates the variation [1].",
            "reference_urls": "https://www.instagram.com/reel/ABC_def12/?utm_source=share",
        },
    )

    assert response.status_code == 302
    reply = topic.posts.exclude(author__email="nobody@example.com").order_by("-created_at").first()
    assert reply is not None
    citation = reply.citations.select_related("reference").get(position=1)
    assert citation.reference.canonical_url == "https://www.instagram.com/reel/ABC_def12/"

    detail = client.get(reverse("discussions:detail", args=[topic.pk]))
    assert b"Provider domain validated" in detail.content
    assert b'rel="noopener noreferrer nofollow ugc"' in detail.content
