import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .parsers import parse_video_url


class VideoReference(models.Model):
    class Provider(models.TextChoices):
        YOUTUBE = "youtube", "YouTube"
        INSTAGRAM = "instagram", "Instagram"

    class Visibility(models.TextChoices):
        UNLISTED = "unlisted", "Unlisted"
        PUBLIC = "public", "Public"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="video_references"
    )
    provider = models.CharField(max_length=20, choices=Provider.choices, editable=False)
    provider_id = models.CharField(max_length=80, editable=False)
    canonical_url = models.URLField(max_length=500, editable=False)
    submitted_url = models.URLField(max_length=2048)
    start_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(2_147_483_647)],
    )
    attribution_name = models.CharField(max_length=160)
    description = models.TextField()
    visibility = models.CharField(
        max_length=20, choices=Visibility.choices, default=Visibility.UNLISTED
    )
    promoted_at = models.DateTimeField(null=True, blank=True, editable=False)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "provider", "provider_id"],
                name="unique_owner_provider_video",
            )
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        parsed = parse_video_url(self.submitted_url)
        self.provider = parsed.provider
        self.provider_id = parsed.provider_id
        self.canonical_url = parsed.canonical_url
        if self.start_seconds is None:
            self.start_seconds = parsed.start_seconds
        if not self.attribution_name.strip() or not self.description.strip():
            raise ValidationError("Attribution and a textual description are required.")

    def can_view(self, user: object, *, via_direct_link: bool = False) -> bool:
        if self.withdrawn_at is not None:
            return False
        if self.visibility == self.Visibility.PUBLIC:
            return True
        return bool(
            via_direct_link or (getattr(user, "is_authenticated", False) and user == self.owner)
        )

    @property
    def is_discoverable(self) -> bool:
        return self.withdrawn_at is None and self.visibility == self.Visibility.PUBLIC

    def promote_public(self) -> None:
        if self.withdrawn_at:
            raise ValidationError("A withdrawn reference cannot be promoted.")
        self.visibility = self.Visibility.PUBLIC
        self.promoted_at = timezone.now()
        self.save(update_fields=["visibility", "promoted_at"])

    @property
    def embed_url(self) -> str | None:
        if self.provider != self.Provider.YOUTUBE:
            return None
        start = f"?start={self.start_seconds}" if self.start_seconds is not None else ""
        return f"https://www.youtube-nocookie.com/embed/{self.provider_id}{start}"
