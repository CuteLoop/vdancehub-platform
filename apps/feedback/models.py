import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class FeedbackRequest(models.Model):
    class DancerRole(models.TextChoices):
        LEADER = "leader", "Leader"
        FOLLOWER = "follower", "Follower"
        SWITCH = "switch", "Switch"
        SOLO = "solo", "Solo"
        OTHER = "other", "Other"

    class SkillLevel(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        IMPROVER = "improver", "Improver"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        PROFESSIONAL = "professional", "Professional"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="feedback_requests"
    )
    video = models.ForeignKey(
        "mediarefs.VideoReference", on_delete=models.PROTECT, related_name="feedback_requests"
    )
    thread = models.OneToOneField(
        "discussions.DiscussionThreadRef",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="feedback_request",
    )
    title = models.CharField(max_length=180)
    goals = models.TextField()
    dancer_role = models.CharField(max_length=20, choices=DancerRole.choices)
    skill_level = models.CharField(max_length=20, choices=SkillLevel.choices)
    footage_consent_confirmed = models.BooleanField(default=False)
    adults_only_confirmed = models.BooleanField(default=False)
    constructive_guidelines_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        if self.video_id and self.author_id and self.video.owner_id != self.author_id:
            raise ValidationError("The request author must own the video reference.")
        if not all(
            (
                self.footage_consent_confirmed,
                self.adults_only_confirmed,
                self.constructive_guidelines_accepted,
            )
        ):
            raise ValidationError("Consent, adult participation, and feedback rules are required.")


class TimestampedFeedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        FeedbackRequest, on_delete=models.CASCADE, related_name="timestamped_feedback"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    post_ref = models.OneToOneField(
        "discussions.DiscussionPostRef", on_delete=models.PROTECT, null=True, blank=True
    )
    seconds = models.PositiveIntegerField()
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
