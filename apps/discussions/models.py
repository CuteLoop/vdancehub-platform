import uuid

from django.conf import settings
from django.db import models


class DiscussionTopic(models.Model):
    class Kind(models.TextChoices):
        QUESTION = "question", "Question"
        FEEDBACK = "feedback", "Feedback"
        RESOURCE = "resource", "Resource"
        DISCUSSION = "discussion", "Discussion"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="discussion_topics"
    )
    title = models.CharField(max_length=180)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    is_closed = models.BooleanField(default=False)
    is_removed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DiscussionPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(DiscussionTopic, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="discussion_posts"
    )
    body = models.TextField()
    is_removed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DiscussionThreadRef(models.Model):
    """Stable domain reference; adapters own translation to a forum backend."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    backend = models.CharField(max_length=40)
    backend_id = models.CharField(max_length=120)
    native_topic = models.OneToOneField(
        DiscussionTopic,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="domain_ref",
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["backend", "backend_id"], name="unique_discussion_backend_thread"
            )
        ]


class DiscussionPostRef(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(
        DiscussionThreadRef, on_delete=models.CASCADE, related_name="post_refs"
    )
    backend_id = models.CharField(max_length=120)
    native_post = models.OneToOneField(
        DiscussionPost,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="domain_ref",
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["thread", "backend_id"], name="unique_discussion_backend_post"
            )
        ]
