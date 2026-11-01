import pytest
from django.core.management import call_command

from apps.discussions.models import DiscussionTopic
from apps.knowledge.models import Movement, MovementRelationship


@pytest.mark.django_db
def test_bachata_demo_seed_is_attributed_and_idempotent() -> None:
    call_command("seed_bachata_demo")
    call_command("seed_bachata_demo")

    topics = DiscussionTopic.objects.filter(
        dance_styles__slug="bachata", tags__slug="move"
    ).distinct()
    assert 25 <= topics.count() <= 50
    cross_body_lead = topics.get(title="Cross Body Lead")
    first_post = cross_body_lead.posts.get()
    assert "Difficulty: 1 of 6" in first_post.body
    citation_urls = set(first_post.citations.values_list("reference__canonical_url", flat=True))
    assert "https://bachatasteps.com/" in citation_urls
    assert "https://www.reddit.com/r/Bachata/comments/1bneys8/" in citation_urls
    assert 25 <= Movement.objects.filter(source_catalog="BachataSteps").count() <= 50
    assert Movement.objects.filter(is_concept=True).count() >= 8
    assert (
        MovementRelationship.objects.filter(status=MovementRelationship.Status.PROPOSED).count()
        >= 20
    )
    mambo = Movement.objects.get(source_catalog="BachataSteps", source_identifier="1590")
    source_titles = set(mambo.references.values_list("title", flat=True))
    assert "Creator source from Dima + Victoria" in source_titles
    reddit = mambo.references.get(hostname="www.reddit.com")
    assert reddit.validation_status == "domain_validated"
