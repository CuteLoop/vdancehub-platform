import uuid

from django.conf import settings
from django.db import models


class KnowledgePage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=180)
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    contributors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="knowledge_contributions"
    )
    discussion = models.ForeignKey(
        "discussions.DiscussionThreadRef", on_delete=models.PROTECT, null=True, blank=True
    )
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class KnowledgeRevision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(KnowledgePage, on_delete=models.CASCADE, related_name="revisions")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = models.TextField()
    edit_summary = models.CharField(max_length=240)
    created_at = models.DateTimeField(auto_now_add=True)
