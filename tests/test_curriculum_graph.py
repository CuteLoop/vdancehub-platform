import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.knowledge.models import (
    Curriculum,
    CurriculumModule,
    CurriculumVersion,
    KnowledgePage,
    ModuleConcept,
    Movement,
    MovementRelationship,
    ReviewedEdition,
)


@pytest.mark.django_db
def test_curriculum_seed_is_attributed_ordered_and_idempotent() -> None:
    call_command("seed_curriculum_pilot")
    call_command("seed_curriculum_pilot")

    assert Curriculum.objects.count() == 3
    assert CurriculumVersion.objects.count() == 3
    assert CurriculumModule.objects.count() == 10
    assert Movement.objects.filter(is_concept=True).count() >= 45
    assert ModuleConcept.objects.count() >= 55
    assert MovementRelationship.objects.filter(status=MovementRelationship.Status.PROPOSED).exists()

    salsa = Curriculum.objects.get(slug="rumba-y-timbal-linear-salsa")
    assert salsa.source.attribution_name == "Rumba y Timbal Dance Studio"
    assert list(salsa.versions.get().modules.values_list("title", flat=True)) == [
        "Beginner",
        "Advanced Beginner",
    ]

    shared_connection = Movement.objects.get(slug="shared-partner-connection")
    assert shared_connection.module_appearances.count() >= 2


@pytest.mark.django_db
def test_curriculum_and_graph_views_connect_modules_concepts_and_sources(client) -> None:
    call_command("seed_curriculum_pilot")

    directory = client.get(reverse("knowledge:curriculum-list"))
    assert directory.status_code == 200
    assert b"Three curriculum pilots" in directory.content
    assert b"MIT Casino Rueda" in directory.content

    detail = client.get(
        reverse("knowledge:curriculum-detail", args=["rumba-y-timbal-linear-salsa"])
    )
    assert detail.status_code == 200
    assert b"Beginner learning path" in detail.content
    assert b"Cross-body lead" in detail.content
    assert b"Community annotated" in detail.content
    assert b'rel="noopener noreferrer nofollow ugc"' in detail.content

    graph = client.get(reverse("knowledge:graph"))
    assert graph.status_code == 200
    assert b"Shared knowledge graph" in graph.content
    assert b"Partner connection" in graph.content
    assert b"Proposed" in graph.content


@pytest.mark.django_db
def test_each_curriculum_has_a_stable_dedicated_discussion_url(client) -> None:
    call_command("seed_curriculum_pilot")

    for slug in (
        "rumba-y-timbal-bachata",
        "rumba-y-timbal-linear-salsa",
        "mit-casino-rueda",
    ):
        response = client.get(reverse("knowledge:curriculum-discussion", args=[slug]))
        assert response.status_code == 200
        assert b"Curriculum conversation" in response.content


@pytest.mark.django_db
def test_curriculum_reply_returns_to_the_readable_discussion_url(client) -> None:
    call_command("seed_curriculum_pilot")
    member = User.objects.create_user(
        email="salsa-member@example.com", password="secret", display_name="Salsa Member"
    )
    member.adult_confirmed_at = timezone.now()
    member.save(update_fields=["adult_confirmed_at"])
    assert client.login(email=member.email, password="secret")

    slug = "rumba-y-timbal-linear-salsa"
    response = client.post(
        reverse("knowledge:curriculum-reply", args=[slug]),
        {"body": "I teach the cross-body lead after connection drills.", "reference_urls": ""},
    )

    assert response.status_code == 302
    assert response.url == reverse("knowledge:curriculum-discussion", args=[slug])


@pytest.mark.django_db
def test_living_pages_and_reviewed_editions_keep_discussion_connected(client) -> None:
    call_command("seed_curriculum_pilot")

    page = KnowledgePage.objects.get(slug="salsa-cross-body-lead")
    assert page.revisions.count() == 1
    assert page.linked_discussions.count() == 1
    assert page.open_to_contributions is True

    response = client.get(reverse("knowledge:page-detail", args=[page.slug]))
    assert response.status_code == 200
    assert b"Living page" in response.content
    assert b"Different approaches" in response.content
    assert b"Continue the discussion" in response.content

    edition = ReviewedEdition.objects.get(slug="bachata-fundamentals-edition-1")
    edition.body = "A changed snapshot"
    with pytest.raises(ValidationError, match="immutable"):
        edition.save()
    edition_response = client.get(
        reverse("knowledge:edition-detail", args=[edition.page.slug, edition.edition_number])
    )
    assert edition_response.status_code == 200
    assert b"Reviewed edition" in edition_response.content
    assert b"not a declaration of universal correctness" in edition_response.content
