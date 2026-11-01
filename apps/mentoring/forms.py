from typing import cast

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.knowledge.models import KnowledgePage
from apps.mediarefs.models import VideoReference

from .models import (
    Enrollment,
    InstructorProfile,
    InstructorReview,
    PracticeAssignment,
    PracticeSubmission,
    PracticeTemplate,
    ReviewAnnotation,
)


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
