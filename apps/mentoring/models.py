import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .validators import validate_external_https_url


class InstructorProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="instructor_profile"
    )
    professional_name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    biography = models.TextField()
    languages = models.JSONField(default=list)
    specialties = models.ManyToManyField("taxonomy.Tag", blank=True)
    remote_available = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self) -> str:
        return self.professional_name


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
    included_reviews = models.PositiveSmallIntegerField(default=1)
    turnaround_days = models.PositiveSmallIntegerField(default=7)
    terms = models.TextField(blank=True)
    booking_link = models.ForeignKey(ExternalLink, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)


class TrainingProgram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor = models.ForeignKey(
        InstructorProfile, on_delete=models.CASCADE, related_name="programs"
    )
    curriculum = models.ForeignKey(
        "knowledge.Curriculum",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="training_programs",
    )
    title = models.CharField(max_length=180)
    summary = models.TextField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class PracticeTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor = models.ForeignKey(
        InstructorProfile, on_delete=models.CASCADE, related_name="practice_templates"
    )
    program = models.ForeignKey(
        TrainingProgram,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="practice_templates",
    )
    title = models.CharField(max_length=180)
    objective = models.TextField()
    instructions = models.TextField()
    evaluation_criteria = models.TextField()
    estimated_minutes = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    linked_pages = models.ManyToManyField(
        "knowledge.KnowledgePage", blank=True, related_name="practice_templates"
    )
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Enrollment(models.Model):
    class Status(models.TextChoices):
        INVITED = "invited", "Invited"
        ACTIVE = "active", "Active"
        ENDED = "ended", "Ended"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor = models.ForeignKey(
        InstructorProfile, on_delete=models.PROTECT, related_name="enrollments"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mentorship_enrollments"
    )
    program = models.ForeignKey(
        TrainingProgram,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrollments",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INVITED)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["instructor", "student"],
                condition=models.Q(status__in=["invited", "active"]),
                name="unique_open_instructor_student_enrollment",
            )
        ]

    def clean(self) -> None:
        if self.instructor_id and self.student_id and self.instructor.user_id == self.student_id:
            raise ValidationError("An instructor cannot enroll themselves as a student.")


class PracticeAssignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        SUBMITTED = "submitted", "Submitted"
        REVIEWED = "reviewed", "Reviewed"
        CANCELED = "canceled", "Canceled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.PROTECT, related_name="assignments")
    template = models.ForeignKey(
        PracticeTemplate, on_delete=models.PROTECT, related_name="assignments"
    )
    due_at = models.DateTimeField(null=True, blank=True)
    personalized_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ASSIGNED)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def clean(self) -> None:
        if (
            self.enrollment_id
            and self.template_id
            and self.enrollment.instructor_id != self.template.instructor_id
        ):
            raise ValidationError(
                "The assignment template must belong to the enrollment instructor."
            )


class PracticeSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.OneToOneField(
        PracticeAssignment, on_delete=models.PROTECT, related_name="submission"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="practice_submissions"
    )
    video = models.ForeignKey(
        "mediarefs.VideoReference", on_delete=models.PROTECT, related_name="practice_submissions"
    )
    self_assessment = models.TextField()
    public_reuse_consent = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def clean(self) -> None:
        if self.assignment_id and self.student_id:
            if self.assignment.enrollment.student_id != self.student_id:
                raise ValidationError("Only the assigned student may submit this practice.")
        if self.video_id and self.student_id and self.video.owner_id != self.student_id:
            raise ValidationError("The student must own the submitted video reference.")


class InstructorReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.OneToOneField(
        PracticeSubmission, on_delete=models.PROTECT, related_name="review"
    )
    instructor = models.ForeignKey(
        InstructorProfile, on_delete=models.PROTECT, related_name="reviews"
    )
    overall_feedback = models.TextField()
    next_steps = models.TextField()
    reviewed_at = models.DateTimeField(default=timezone.now)

    def clean(self) -> None:
        if (
            self.submission_id
            and self.instructor_id
            and self.submission.assignment.enrollment.instructor_id != self.instructor_id
        ):
            raise ValidationError("Only the assigned instructor may review this submission.")


class ReviewAnnotation(models.Model):
    class Category(models.TextChoices):
        TIMING = "timing", "Timing"
        CONNECTION = "connection", "Connection"
        BALANCE = "balance", "Balance"
        TECHNIQUE = "technique", "Technique"
        MUSICALITY = "musicality", "Musicality"
        NEXT_STEP = "next_step", "Next step"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(
        InstructorReview, on_delete=models.CASCADE, related_name="annotations"
    )
    seconds = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    category = models.CharField(max_length=30, choices=Category.choices)
    body = models.TextField()

    class Meta:
        ordering = ["seconds", "id"]

    @property
    def timestamp(self) -> str:
        minutes, seconds = divmod(self.seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"


class PracticeJournal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="practice_journal"
    )
    practice_date = models.DateField()
    minutes = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    notes = models.TextField()
    video = models.ForeignKey(
        "mediarefs.VideoReference",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="journal_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-practice_date", "-created_at"]
