import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .references import classify_reference_url


class SourceReference(models.Model):
    class Provider(models.TextChoices):
        INSTAGRAM = "instagram", "Instagram"
        YOUTUBE = "youtube", "YouTube"
        WEBSITE = "website", "Website"

    class Status(models.TextChoices):
        DOMAIN_VALIDATED = "domain_validated", "Provider domain validated"
        UNREVIEWED = "unreviewed", "External link — unreviewed"
        MODERATOR_REVIEWED = "moderator_reviewed", "Moderator reviewed"
        BLOCKED = "blocked", "Blocked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submitted_url = models.URLField(max_length=2048)
    canonical_url = models.URLField(max_length=2048, editable=False)
    hostname = models.CharField(max_length=253, editable=False)
    provider = models.CharField(max_length=20, choices=Provider.choices, editable=False)
    validation_status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.UNREVIEWED
    )
    title = models.CharField(max_length=180)
    attribution_name = models.CharField(max_length=160)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="source_references"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_source_references",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["canonical_url", "attribution_name"],
                name="unique_canonical_attributed_reference",
            )
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        classified = classify_reference_url(self.submitted_url)
        self.canonical_url = classified.canonical_url
        self.hostname = classified.hostname
        self.provider = classified.provider
        if not self.pk or self.validation_status not in {
            self.Status.MODERATOR_REVIEWED,
            self.Status.BLOCKED,
        }:
            self.validation_status = classified.validation_status
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_clickable(self) -> bool:
        return self.validation_status in {
            self.Status.DOMAIN_VALIDATED,
            self.Status.MODERATOR_REVIEWED,
        }

    def review(self, *, reviewer: object, approve: bool) -> None:
        from django.utils import timezone

        if not getattr(reviewer, "is_staff", False):
            raise PermissionDenied("Only staff may review external references.")
        self.validation_status = self.Status.MODERATOR_REVIEWED if approve else self.Status.BLOCKED
        self.reviewed_by = reviewer  # type: ignore[assignment]
        self.reviewed_at = timezone.now()
        self.save(update_fields=["validation_status", "reviewed_by", "reviewed_at"])


class PostCitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        "discussions.DiscussionPost", on_delete=models.CASCADE, related_name="citations"
    )
    reference = models.ForeignKey(
        SourceReference, on_delete=models.PROTECT, related_name="post_citations"
    )
    position = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["post", "position"], name="unique_post_citation_position"
            )
        ]


class Movement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True)
    dance_style = models.ForeignKey(
        "taxonomy.DanceStyle", on_delete=models.PROTECT, related_name="movements"
    )
    summary = models.TextField()
    difficulty = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(6)]
    )
    is_concept = models.BooleanField(default=False)
    tags = models.ManyToManyField("taxonomy.Tag", blank=True, related_name="movements")
    references = models.ManyToManyField(SourceReference, blank=True, related_name="movements")
    discussion = models.OneToOneField(
        "discussions.DiscussionThreadRef",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movement",
    )
    source_catalog = models.CharField(max_length=80, blank=True)
    source_identifier = models.CharField(max_length=80, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["difficulty", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_catalog", "source_identifier"],
                condition=~models.Q(source_catalog="") & ~models.Q(source_identifier=""),
                name="unique_movement_catalog_identifier",
            )
        ]

    def __str__(self) -> str:
        return self.name


class MovementAlias(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movement = models.ForeignKey(Movement, on_delete=models.CASCADE, related_name="name_aliases")
    name = models.CharField(max_length=180)
    locale = models.CharField(max_length=20, blank=True)
    school_or_region = models.CharField(max_length=120, blank=True)
    source = models.ForeignKey(SourceReference, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["movement", "name", "school_or_region"],
                name="unique_movement_alias_context",
            )
        ]


class MovementRelationship(models.Model):
    class Kind(models.TextChoices):
        PREREQUISITE = "prerequisite", "Prerequisite"
        COMPONENT = "component", "Contains component"
        VARIATION = "variation", "Variation"
        RELATED = "related", "Related"

    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        ACCEPTED = "accepted", "Community accepted"
        DISPUTED = "disputed", "Disputed"

    class Provenance(models.TextChoices):
        CURATED = "curated", "Curated"
        IMPORTED = "imported", "Imported"
        INFERRED = "inferred", "Name-based inference"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_movement = models.ForeignKey(
        Movement, on_delete=models.CASCADE, related_name="outgoing_relationships"
    )
    to_movement = models.ForeignKey(
        Movement, on_delete=models.CASCADE, related_name="incoming_relationships"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROPOSED)
    provenance = models.CharField(max_length=20, choices=Provenance.choices)
    note = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_movement", "to_movement", "kind"],
                name="unique_movement_relationship",
            ),
            models.CheckConstraint(
                condition=~models.Q(from_movement=models.F("to_movement")),
                name="movement_relationship_not_self",
            ),
        ]


class Curriculum(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True)
    dance_style = models.ForeignKey(
        "taxonomy.DanceStyle", on_delete=models.PROTECT, related_name="curricula"
    )
    organization = models.CharField(max_length=180)
    summary = models.TextField()
    source = models.ForeignKey(SourceReference, on_delete=models.PROTECT, related_name="curricula")
    discussion = models.OneToOneField(
        "discussions.DiscussionThreadRef",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="curriculum",
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class CurriculumVersion(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published source"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name="versions")
    label = models.CharField(max_length=80)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    note = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["curriculum", "label"], name="unique_curriculum_version_label"
            )
        ]


class CurriculumModule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(CurriculumVersion, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180)
    summary = models.TextField(blank=True)
    position = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["position", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["version", "slug"], name="unique_curriculum_module_slug"
            ),
            models.UniqueConstraint(
                fields=["version", "position"], name="unique_curriculum_module_position"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.version.curriculum.name}: {self.title}"


class ModuleConcept(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(
        CurriculumModule, on_delete=models.CASCADE, related_name="concept_entries"
    )
    concept = models.ForeignKey(
        Movement, on_delete=models.PROTECT, related_name="module_appearances"
    )
    position = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    note = models.CharField(max_length=240, blank=True)
    source = models.ForeignKey(
        SourceReference,
        on_delete=models.PROTECT,
        related_name="module_concepts",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["position", "concept__name"]
        constraints = [
            models.UniqueConstraint(fields=["module", "concept"], name="unique_module_concept"),
            models.UniqueConstraint(
                fields=["module", "position"], name="unique_module_concept_position"
            ),
        ]


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
