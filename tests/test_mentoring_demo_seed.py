import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.mentoring.models import (
    InstructorProfile,
    InstructorReview,
    MentoringOffer,
    MentoringRequest,
    PracticeAssignment,
    PracticeJournal,
    PracticeSubmission,
    PracticeTemplate,
    ReviewAnnotation,
    TrainingProgram,
)


@pytest.mark.django_db
def test_mentoring_demo_seed_builds_complete_idempotent_workflow() -> None:
    options = {
        "mentor_password": "Mentor-demo-password-83",
        "student_password": "Student-demo-password-47",
    }
    call_command("seed_mentoring_demo", **options)

    mentor = User.objects.get(email="demo-mentor@vdancehub.local")
    student = User.objects.get(email="demo-student@vdancehub.local")
    assert mentor.check_password(options["mentor_password"])
    assert student.check_password(options["student_password"])
    assert InstructorProfile.objects.filter(is_published=True).count() == 3
    assert MentoringOffer.objects.filter(is_active=True).count() == 4
    assert PracticeTemplate.objects.filter(is_public=True).count() >= 6
    assert TrainingProgram.objects.count() == 1
    assert PracticeAssignment.objects.count() == 3
    assert PracticeSubmission.objects.count() == 2
    assert InstructorReview.objects.count() == 1
    assert ReviewAnnotation.objects.count() == 2
    assert MentoringRequest.objects.filter(status="requested").count() == 1
    assert PracticeJournal.objects.filter(student=student).count() == 3

    snapshot = {
        "users": User.objects.count(),
        "offers": MentoringOffer.objects.count(),
        "assignments": PracticeAssignment.objects.count(),
        "submissions": PracticeSubmission.objects.count(),
        "journal": PracticeJournal.objects.count(),
    }
    call_command("seed_mentoring_demo", **options)
    assert snapshot == {
        "users": User.objects.count(),
        "offers": MentoringOffer.objects.count(),
        "assignments": PracticeAssignment.objects.count(),
        "submissions": PracticeSubmission.objects.count(),
        "journal": PracticeJournal.objects.count(),
    }
