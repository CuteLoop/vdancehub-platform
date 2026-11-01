import pytest
from django.core.management import call_command

from apps.discussions.models import DiscussionTopic


@pytest.mark.django_db
def test_bachata_demo_seed_is_attributed_and_idempotent() -> None:
    call_command("seed_bachata_demo")
    call_command("seed_bachata_demo")

    topics = DiscussionTopic.objects.filter(
        dance_styles__slug="bachata", tags__slug="move"
    ).distinct()
    assert topics.count() == 5
    cross_body_lead = topics.get(title="Cross Body Lead")
    first_post = cross_body_lead.posts.get()
    assert "BachataSteps.com" in first_post.body
    assert "reddit.com/r/Bachata/comments/1bneys8" in first_post.body
    assert "Difficulty: 1 of 6" in first_post.body
