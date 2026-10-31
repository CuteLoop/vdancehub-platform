import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils import timezone

from .validators import validate_external_https_url


class InstructorProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="instructor_profile"
    )
    professional_name = models.CharField(max_length=160)
    biography = models.TextField()
    languages = models.JSONField(default=list)
    specialties = models.ManyToManyField("taxonomy.Tag", blank=True)
    remote_available = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)


class ExternalLink(models.Model):
    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    url = models.URLField(max_length=2048)
    label = models.CharField(max_length=120)
    status = models.CharField(
        max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_external_links",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        validate_external_https_url(self.url)

    def approve(self, *, moderator: object) -> None:
        if not getattr(moderator, "is_staff", False):
            raise PermissionDenied("Only staff may approve external links.")
        self.status = self.ReviewStatus.APPROVED
        self.reviewed_by = moderator  # type: ignore[assignment]
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "reviewed_by", "reviewed_at"])


class MentoringOffer(models.Model):
    class Format(models.TextChoices):
        VIDEO_REVIEW = "video_review", "Asynchronous video review"
        PRIVATE_LESSON = "private_lesson", "Private online lesson"
        PROGRAM = "program", "Multi-session program"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor = models.ForeignKey(
        InstructorProfile, on_delete=models.CASCADE, related_name="offers"
    )
    title = models.CharField(max_length=160)
    description = models.TextField()
    format = models.CharField(max_length=30, choices=Format.choices)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_currency = models.CharField(max_length=3, blank=True)
    booking_link = models.ForeignKey(ExternalLink, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
