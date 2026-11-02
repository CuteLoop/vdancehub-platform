from typing import Any, cast

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.knowledge.models import KnowledgePage
from apps.mediarefs.models import VideoReference

from .models import (
    Enrollment,
    ExternalLink,
    InstructorProfile,
    InstructorReview,
    MentoringOffer,
    MentoringRequest,
    PracticeAssignment,
    PracticeJournal,
    PracticeSubmission,
    PracticeTemplate,
    ReviewAnnotation,
)
from .validators import validate_external_https_url


class InstructorProfileForm(forms.Form):
    professional_name = forms.CharField(max_length=160)
    slug = forms.SlugField(max_length=180)
    biography = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}))
    languages = forms.CharField(help_text="Comma-separated languages.")
    remote_available = forms.BooleanField(required=False, initial=True)
    is_published = forms.BooleanField(required=False, label="Publish my mentor profile")

    def __init__(self, *args: object, profile: InstructorProfile | None = None, **kwargs: object):
        self.profile = profile
        if profile is not None and "initial" not in kwargs:
            kwargs["initial"] = {
                "professional_name": profile.professional_name,
                "slug": profile.slug,
                "biography": profile.biography,
                "languages": ", ".join(profile.languages),
                "remote_available": profile.remote_available,
                "is_published": profile.is_published,
            }
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]

    def clean_slug(self) -> str:
        slug = cast(str, self.cleaned_data["slug"])
        existing = InstructorProfile.objects.filter(slug=slug)
        if self.profile is not None:
            existing = existing.exclude(pk=self.profile.pk)
        if existing.exists():
            raise ValidationError("This mentor URL is already in use.")
        return slug

    def save(self, *, user: User) -> InstructorProfile:
        languages = [
            language.strip()
            for language in self.cleaned_data["languages"].split(",")
            if language.strip()
        ]
        profile, _ = InstructorProfile.objects.update_or_create(
            user=user,
            defaults={
                "professional_name": self.cleaned_data["professional_name"],
                "slug": self.cleaned_data["slug"],
                "biography": self.cleaned_data["biography"],
                "languages": languages,
                "remote_available": self.cleaned_data["remote_available"],
                "is_published": self.cleaned_data["is_published"],
            },
        )
        return profile


class PracticeTemplateForm(forms.ModelForm):  # type: ignore[type-arg]
    linked_pages = forms.ModelMultipleChoiceField(
        queryset=KnowledgePage.objects.filter(is_published=True), required=False
    )

    class Meta:
        model = PracticeTemplate
        fields = (
            "title",
            "objective",
            "instructions",
            "evaluation_criteria",
            "estimated_minutes",
            "linked_pages",
            "is_public",
        )
        widgets = {
            "objective": forms.Textarea(attrs={"rows": 3}),
            "instructions": forms.Textarea(attrs={"rows": 6}),
            "evaluation_criteria": forms.Textarea(attrs={"rows": 3}),
        }

    def save_for(self, *, instructor: InstructorProfile) -> PracticeTemplate:
        template = self.save(commit=False)
        template.instructor = instructor
        template.full_clean(exclude={"linked_pages"})
        template.save()
        self.save_m2m()
        return cast(PracticeTemplate, template)


class MentoringOfferForm(forms.ModelForm):  # type: ignore[type-arg]
    booking_url = forms.URLField(max_length=2048, assume_scheme="https")
    booking_label = forms.CharField(max_length=120, initial="Book with instructor")

    class Meta:
        model = MentoringOffer
        fields = (
            "title",
            "description",
            "format",
            "price_amount",
            "price_currency",
            "included_reviews",
            "turnaround_days",
            "terms",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "terms": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_booking_url(self) -> str:
        url = cast(str, self.cleaned_data["booking_url"])
        validate_external_https_url(url)
        return url

    def clean_price_currency(self) -> str:
        currency = cast(str, self.cleaned_data["price_currency"]).upper().strip()
        if self.cleaned_data.get("price_amount") and len(currency) != 3:
            raise ValidationError("Use a three-letter currency code such as USD or EUR.")
        return currency

    @transaction.atomic
    def save_for(self, *, instructor: InstructorProfile) -> MentoringOffer:
        link = ExternalLink.objects.create(
            owner=instructor.user,
            url=self.cleaned_data["booking_url"],
            label=self.cleaned_data["booking_label"],
        )
        offer = self.save(commit=False)
        offer.instructor = instructor
        offer.booking_link = link
        offer.full_clean()
        offer.save()
        return cast(MentoringOffer, offer)


class MentoringRequestForm(forms.ModelForm):  # type: ignore[type-arg]
    class Meta:
        model = MentoringRequest
        fields = ("offer", "focus")
        widgets = {"focus": forms.Textarea(attrs={"rows": 5})}
        labels = {"focus": "What would you like help with?"}

    def __init__(
        self,
        *args: object,
        instructor: InstructorProfile,
        student: User,
        **kwargs: object,
    ):
        self.instructor = instructor
        self.student = student
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        offer_field = self.fields["offer"]
        assert isinstance(offer_field, forms.ModelChoiceField)
        offer_field.queryset = instructor.offers.filter(
            is_active=True, format=MentoringOffer.Format.VIDEO_REVIEW
        )

    def clean_offer(self) -> MentoringOffer:
        offer = cast(MentoringOffer, self.cleaned_data["offer"])
        if MentoringRequest.objects.filter(
            offer=offer,
            student=self.student,
            status=MentoringRequest.Status.REQUESTED,
        ).exists():
            raise ValidationError("You already have a pending request for this offer.")
        return offer

    def save_for(self, *, student: User) -> MentoringRequest:
        mentoring_request = self.save(commit=False)
        mentoring_request.student = student
        mentoring_request.full_clean()
        mentoring_request.save()
        return cast(MentoringRequest, mentoring_request)


class AcceptMentoringRequestForm(forms.Form):
    template = forms.ModelChoiceField(queryset=PracticeTemplate.objects.none())
    due_at = forms.DateTimeField(
        required=False, widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    instructor_note = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args: object, instructor: InstructorProfile, **kwargs: object):
        self.instructor = instructor
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        template_field = self.fields["template"]
        assert isinstance(template_field, forms.ModelChoiceField)
        template_field.queryset = instructor.practice_templates.all()

    @transaction.atomic
    def save(self, *, mentoring_request: MentoringRequest) -> PracticeAssignment:
        enrollment = Enrollment.objects.filter(
            instructor=self.instructor,
            student=mentoring_request.student,
            status__in=[Enrollment.Status.INVITED, Enrollment.Status.ACTIVE],
        ).first()
        if enrollment is None:
            enrollment = Enrollment.objects.create(
                instructor=self.instructor,
                student=mentoring_request.student,
                status=Enrollment.Status.ACTIVE,
            )
        elif enrollment.status == Enrollment.Status.INVITED:
            enrollment.status = Enrollment.Status.ACTIVE
            enrollment.save(update_fields=["status"])

        assignment = PracticeAssignment(
            enrollment=enrollment,
            template=self.cleaned_data["template"],
            due_at=self.cleaned_data["due_at"],
            personalized_notes=self.cleaned_data["instructor_note"],
        )
        assignment.full_clean()
        assignment.save()
        mentoring_request.status = MentoringRequest.Status.ACCEPTED
        mentoring_request.instructor_note = self.cleaned_data["instructor_note"]
        mentoring_request.assignment = assignment
        mentoring_request.responded_at = timezone.now()
        mentoring_request.full_clean()
        mentoring_request.save(
            update_fields=["status", "instructor_note", "assignment", "responded_at"]
        )
        return assignment


class AssignmentInviteForm(forms.Form):
    student_email = forms.EmailField(help_text="The student must already have a VDanceHub account.")
    template = forms.ModelChoiceField(queryset=PracticeTemplate.objects.none())
    due_at = forms.DateTimeField(
        required=False, widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    personalized_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args: object, instructor: InstructorProfile, **kwargs: object):
        self.instructor = instructor
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        template_field = self.fields["template"]
        assert isinstance(template_field, forms.ModelChoiceField)
        template_field.queryset = instructor.practice_templates.all()

    def clean_student_email(self) -> str:
        email = cast(str, self.cleaned_data["student_email"]).lower()
        try:
            student = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise ValidationError("No VDanceHub account uses this email address.") from exc
        if student.adult_confirmed_at is None:
            raise ValidationError("The student must confirm they are an adult.")
        if student == self.instructor.user:
            raise ValidationError("You cannot assign practice to yourself.")
        return email

    @transaction.atomic
    def save(self) -> PracticeAssignment:
        student = User.objects.get(email__iexact=self.cleaned_data["student_email"])
        enrollment = Enrollment.objects.filter(
            instructor=self.instructor,
            student=student,
            status__in=[Enrollment.Status.INVITED, Enrollment.Status.ACTIVE],
        ).first()
        if enrollment is None:
            enrollment = Enrollment.objects.create(
                instructor=self.instructor,
                student=student,
                status=Enrollment.Status.ACTIVE,
            )
        elif enrollment.status == Enrollment.Status.INVITED:
            enrollment.status = Enrollment.Status.ACTIVE
            enrollment.save(update_fields=["status"])
        assignment = PracticeAssignment(
            enrollment=enrollment,
            template=self.cleaned_data["template"],
            due_at=self.cleaned_data["due_at"],
            personalized_notes=self.cleaned_data["personalized_notes"],
        )
        assignment.full_clean()
        assignment.save()
        return assignment


class PracticeSubmissionForm(forms.Form):
    video_url = forms.URLField(max_length=2048, assume_scheme="https")
    video_description = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    self_assessment = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}))

    @transaction.atomic
    def save(self, *, assignment: PracticeAssignment, student: User) -> PracticeSubmission:
        video = VideoReference.objects.create(
            owner=student,
            submitted_url=self.cleaned_data["video_url"],
            attribution_name=student.display_name,
            description=self.cleaned_data["video_description"],
            visibility=VideoReference.Visibility.UNLISTED,
        )
        submission = PracticeSubmission(
            assignment=assignment,
            student=student,
            video=video,
            self_assessment=self.cleaned_data["self_assessment"],
        )
        submission.full_clean()
        submission.save()
        assignment.status = PracticeAssignment.Status.SUBMITTED
        assignment.save(update_fields=["status"])
        return submission


class PracticeJournalForm(forms.ModelForm):  # type: ignore[type-arg]
    video_url = forms.URLField(max_length=2048, required=False, assume_scheme="https")
    video_description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    class Meta:
        model = PracticeJournal
        fields = ("practice_date", "minutes", "notes")
        widgets = {
            "practice_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean() or {}
        if cleaned_data.get("video_url") and not cleaned_data.get("video_description"):
            self.add_error("video_description", "Describe the optional practice video.")
        return cleaned_data

    @transaction.atomic
    def save_for(self, *, student: User) -> PracticeJournal:
        video = None
        if self.cleaned_data.get("video_url"):
            video = VideoReference.objects.create(
                owner=student,
                submitted_url=self.cleaned_data["video_url"],
                attribution_name=student.display_name,
                description=self.cleaned_data["video_description"],
                visibility=VideoReference.Visibility.UNLISTED,
            )
        entry = self.save(commit=False)
        entry.student = student
        entry.video = video
        entry.full_clean()
        entry.save()
        return cast(PracticeJournal, entry)


class InstructorReviewForm(forms.Form):
    overall_feedback = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}))
    next_steps = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))
    annotations = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "23|timing|Observation"}),
        help_text="One per line: seconds|category|observation",
    )

    def clean_annotations(self) -> list[tuple[int, str, str]]:
        parsed: list[tuple[int, str, str]] = []
        allowed = {choice for choice, _ in ReviewAnnotation.Category.choices}
        for line in self.cleaned_data["annotations"].splitlines():
            if not line.strip():
                continue
            parts = [part.strip() for part in line.split("|", 2)]
            if len(parts) != 3 or not parts[0].isdigit() or parts[1] not in allowed or not parts[2]:
                raise ValidationError("Use seconds|category|observation for each annotation.")
            parsed.append((int(parts[0]), parts[1], parts[2]))
        return parsed

    @transaction.atomic
    def save(
        self, *, submission: PracticeSubmission, instructor: InstructorProfile
    ) -> InstructorReview:
        review = InstructorReview(
            submission=submission,
            instructor=instructor,
            overall_feedback=self.cleaned_data["overall_feedback"],
            next_steps=self.cleaned_data["next_steps"],
        )
        review.full_clean()
        review.save()
        ReviewAnnotation.objects.bulk_create(
            [
                ReviewAnnotation(review=review, seconds=seconds, category=category, body=body)
                for seconds, category, body in self.cleaned_data["annotations"]
            ]
        )
        assignment = submission.assignment
        assignment.status = PracticeAssignment.Status.REVIEWED
        assignment.save(update_fields=["status"])
        return review
