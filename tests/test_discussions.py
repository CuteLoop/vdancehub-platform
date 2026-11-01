import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.discussions.models import DiscussionPost, DiscussionPostRef, DiscussionTopic
from apps.discussions.services import create_topic_with_first_post
from apps.taxonomy.models import DanceStyle, Tag


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


@pytest.mark.django_db
def test_discussion_directory_filters_topics_by_style_and_tag(client) -> None:
    author = User.objects.create_user(
        email="curator@example.com", password="secret", display_name="Curator"
    )
    bachata = DanceStyle.objects.create(name="Bachata", slug="bachata")
    move = Tag.objects.create(name="Move", slug="move")
    thread_ref = create_topic_with_first_post(
        author=author,
        title="Cross Body Lead",
        kind=DiscussionTopic.Kind.RESOURCE,
        body="A beginner movement reference.",
    )
    topic = thread_ref.native_topic
    assert topic is not None
    topic.dance_styles.add(bachata)
    topic.tags.add(move)
    create_topic_with_first_post(
        author=author,
        title="Cumbia timing",
        kind=DiscussionTopic.Kind.QUESTION,
        body="How should I count it?",
    )

    response = client.get(reverse("discussions:list"), {"style": "bachata", "tag": "move"})

    assert response.status_code == 200
    assert b"Cross Body Lead" in response.content
    assert b"Cumbia timing" not in response.content


@pytest.mark.django_db
def test_topic_detail_escapes_posts_and_allows_authenticated_replies(client) -> None:
    author = User.objects.create_user(
        email="author@example.com", password="secret", display_name="Author"
    )
    reader = User.objects.create_user(
        email="reader@example.com",
        password="secret",
        display_name="Reader",
        adult_confirmed_at=timezone.now(),
    )
    thread_ref = create_topic_with_first_post(
        author=author,
        title="Pico Pico",
        kind=DiscussionTopic.Kind.RESOURCE,
        body="<script>alert('no')</script> What terminology do you use?",
    )
    topic = thread_ref.native_topic
    assert topic is not None

    detail_response = client.get(reverse("discussions:detail", args=[topic.pk]))
    assert detail_response.status_code == 200
    assert b"&lt;script&gt;" in detail_response.content
    assert b"<script>" not in detail_response.content

    assert client.login(email=reader.email, password="secret")
    reply_response = client.post(
        reverse("discussions:reply", args=[topic.pk]),
        {"body": "I learned this under a different name."},
    )

    assert reply_response.status_code == 302
    reply = DiscussionPost.objects.get(topic=topic, author=reader)
    assert reply.body == "I learned this under a different name."
    assert DiscussionPostRef.objects.filter(native_post=reply).exists()


@pytest.mark.django_db
def test_reply_requires_login_adult_confirmation_and_open_topic(client) -> None:
    author = User.objects.create_user(
        email="author@example.com", password="secret", display_name="Author"
    )
    thread_ref = create_topic_with_first_post(
        author=author,
        title="Mambo side-to-side",
        kind=DiscussionTopic.Kind.RESOURCE,
        body="How do you teach the weight transfer?",
    )
    topic = thread_ref.native_topic
    assert topic is not None
    reply_url = reverse("discussions:reply", args=[topic.pk])

    anonymous_response = client.post(reply_url, {"body": "Anonymous reply"})
    assert anonymous_response.status_code == 302
    assert "/accounts/login/" in anonymous_response.url

    underage_unconfirmed = User.objects.create_user(
        email="unconfirmed@example.com", password="secret", display_name="Unconfirmed"
    )
    assert client.login(email=underage_unconfirmed.email, password="secret")
    assert client.post(reply_url, {"body": "Reply"}).status_code == 403

    underage_unconfirmed.adult_confirmed_at = timezone.now()
    underage_unconfirmed.save(update_fields=["adult_confirmed_at"])
    topic.is_closed = True
    topic.save(update_fields=["is_closed"])
    assert client.post(reply_url, {"body": "Reply"}).status_code == 403
