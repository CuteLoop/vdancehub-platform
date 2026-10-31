from django.db import transaction

from apps.accounts.models import User

from .models import DiscussionPost, DiscussionPostRef, DiscussionThreadRef, DiscussionTopic


@transaction.atomic
def create_topic_with_first_post(
    *, author: User, title: str, kind: str, body: str
) -> DiscussionThreadRef:
    topic = DiscussionTopic.objects.create(author=author, title=title, kind=kind)
    post = DiscussionPost.objects.create(topic=topic, author=author, body=body)
    thread_ref = DiscussionThreadRef.objects.create(
        backend="native",
        backend_id=str(topic.pk),
        native_topic=topic,
        created_by=author,
    )
    DiscussionPostRef.objects.create(
        thread=thread_ref,
        backend_id=str(post.pk),
        native_post=post,
        author=author,
    )
    return thread_ref
