import uuid

from django.conf import settings
from django.db import models


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=180)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    contributors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="projects"
    )
    discussions = models.ManyToManyField("discussions.DiscussionThreadRef", blank=True)
    video_references = models.ManyToManyField("mediarefs.VideoReference", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ProjectMilestone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class CommunityClassProposal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    title = models.CharField(max_length=180)
    description = models.TextField()
    funding_target = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    external_funding_link = models.ForeignKey(
        "mentoring.ExternalLink", on_delete=models.PROTECT, null=True, blank=True
    )
    is_public = models.BooleanField(default=False)
