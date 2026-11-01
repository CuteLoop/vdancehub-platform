from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User

from .forms import (
    AssignmentInviteForm,
    InstructorProfileForm,
    InstructorReviewForm,
    PracticeSubmissionForm,
    PracticeTemplateForm,
)
from .models import (
    Enrollment,
    InstructorProfile,
    PracticeAssignment,
    PracticeSubmission,
)


def _private(response: HttpResponse) -> HttpResponse:
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["Cache-Control"] = "private, no-store"
    return response


def mentor_directory(request: HttpRequest) -> HttpResponse:
    profiles = (
        InstructorProfile.objects.filter(is_published=True)
        .prefetch_related("specialties", "offers__booking_link", "practice_templates")
        .order_by("professional_name")
    )
    return render(request, "mentoring/directory.html", {"profiles": profiles})


def mentor_profile(request: HttpRequest, slug: str) -> HttpResponse:
    profile = get_object_or_404(
        InstructorProfile.objects.filter(is_published=True).prefetch_related(
            "specialties",
            "offers__booking_link",
            "practice_templates__linked_pages",
        ),
        slug=slug,
    )
    return render(request, "mentoring/profile.html", {"profile": profile})


@login_required
def become_a_mentor(request: HttpRequest) -> HttpResponse:
    assert isinstance(request.user, User)
    if request.user.adult_confirmed_at is None:
        raise Http404
    profile = InstructorProfile.objects.filter(user=request.user).first()
    form = InstructorProfileForm(request.POST or None, profile=profile)
    if request.method == "POST" and form.is_valid():
        form.save(user=request.user)
        return redirect("mentoring:studio")
    return _private(render(request, "mentoring/become.html", {"form": form}))


@login_required
def instructor_studio(request: HttpRequest) -> HttpResponse:
    assert isinstance(request.user, User)
    instructor = get_object_or_404(InstructorProfile, user=request.user)
    pending = (
        PracticeSubmission.objects.filter(
            assignment__enrollment__instructor=instructor,
            review__isnull=True,
        )
        .select_related("student", "assignment__template", "video")
        .order_by("submitted_at")
    )
    context = {
        "instructor": instructor,
        "pending": pending,
        "active_students": Enrollment.objects.filter(
            instructor=instructor, status=Enrollment.Status.ACTIVE
        ).count(),
        "program_count": instructor.programs.count(),
        "templates": instructor.practice_templates.prefetch_related("linked_pages"),
    }
    return _private(render(request, "mentoring/studio.html", context))


@login_required
def create_practice_template(request: HttpRequest) -> HttpResponse:
    assert isinstance(request.user, User)
    instructor = get_object_or_404(InstructorProfile, user=request.user)
    form = PracticeTemplateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save_for(instructor=instructor)
        return redirect("mentoring:studio")
    return _private(render(request, "mentoring/template_form.html", {"form": form}))


@login_required
def create_assignment(request: HttpRequest) -> HttpResponse:
    assert isinstance(request.user, User)
    instructor = get_object_or_404(InstructorProfile, user=request.user)
    form = AssignmentInviteForm(request.POST or None, instructor=instructor)
    if request.method == "POST" and form.is_valid():
        assignment = form.save()
        return redirect("mentoring:assignment-detail", pk=assignment.pk)
    return _private(render(request, "mentoring/assignment_form.html", {"form": form}))


@login_required
def student_dashboard(request: HttpRequest) -> HttpResponse:
    assert isinstance(request.user, User)
    assignments = (
        PracticeAssignment.objects.filter(enrollment__student=request.user)
        .select_related("template", "enrollment__instructor")
        .order_by("status", "due_at", "-assigned_at")
    )
    return _private(
        render(request, "mentoring/student_dashboard.html", {"assignments": assignments})
    )


@login_required
def assignment_detail(request: HttpRequest, pk: str) -> HttpResponse:
    assert isinstance(request.user, User)
    assignment = get_object_or_404(
        PracticeAssignment.objects.filter(
            Q(enrollment__student=request.user) | Q(enrollment__instructor__user=request.user)
        )
        .select_related(
            "template",
            "enrollment__student",
            "enrollment__instructor",
            "submission__video",
            "submission__review",
        )
        .prefetch_related(
            "template__linked_pages",
            "submission__review__annotations",
        ),
        pk=pk,
    )
    return _private(render(request, "mentoring/assignment_detail.html", {"assignment": assignment}))


@login_required
def submit_practice(request: HttpRequest, pk: str) -> HttpResponse:
    assert isinstance(request.user, User)
    assignment = get_object_or_404(
        PracticeAssignment.objects.select_related("enrollment", "template"),
        pk=pk,
        enrollment__student=request.user,
        status=PracticeAssignment.Status.ASSIGNED,
    )
    form = PracticeSubmissionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            form.save(assignment=assignment, student=request.user)
        except ValidationError as exc:
            form.add_error("video_url", exc)
        else:
            return redirect("mentoring:assignment-detail", pk=assignment.pk)
    return _private(
        render(
            request,
            "mentoring/submission_form.html",
            {"assignment": assignment, "form": form},
        )
    )


@login_required
def review_submission(request: HttpRequest, pk: str) -> HttpResponse:
    assert isinstance(request.user, User)
    instructor = get_object_or_404(InstructorProfile, user=request.user)
    submission = get_object_or_404(
        PracticeSubmission.objects.filter(
            assignment__enrollment__instructor=instructor,
            review__isnull=True,
        ).select_related("student", "video", "assignment__template"),
        pk=pk,
    )
    form = InstructorReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save(submission=submission, instructor=instructor)
        return redirect("mentoring:assignment-detail", pk=submission.assignment_id)
    return _private(
        render(
            request,
            "mentoring/review_form.html",
            {"submission": submission, "form": form},
        )
    )
