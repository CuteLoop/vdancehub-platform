import pytest

from apps.accounts.models import User
from apps.discussions.models import DiscussionTopic
from apps.discussions.services import create_topic_with_first_post


@pytest.mark.django_db
def test_native_topic_and_first_post_receive_stable_domain_references() -> None:
    author = User.objects.create_user(
        email="author@example.com", password="secret", display_name="Author"
    )
    thread_ref = create_topic_with_first_post(
        author=author,
        title="How should I practice timing?",
        kind=DiscussionTopic.Kind.QUESTION,
        body="I would like a fundamentals-focused practice plan.",
    )
    assert thread_ref.backend == "native"
    assert thread_ref.native_topic is not None
    assert thread_ref.native_topic.title == "How should I practice timing?"
    assert thread_ref.post_refs.get().native_post.body.startswith("I would like")
