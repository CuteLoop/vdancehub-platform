import pytest
from django.core.management import call_command
from django.urls import reverse

from apps.knowledge.models import (
    Curriculum,
    CurriculumModule,
    CurriculumVersion,
    ModuleConcept,
    Movement,
    MovementRelationship,
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
