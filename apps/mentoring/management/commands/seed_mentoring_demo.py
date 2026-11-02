from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.knowledge.models import Curriculum, KnowledgePage
from apps.mediarefs.models import VideoReference
from apps.mentoring.models import (
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
    TrainingProgram,
)


class Command(BaseCommand):
    help = "Create clearly labeled fictional mentorship data for product demonstrations."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--mentor-password", default="")
        parser.add_argument("--student-password", default="")

    def _user(
        self,
        *,
        email: str,
        display_name: str,
        password: str = "",
        is_staff: bool = False,
    ) -> User:
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"display_name": display_name, "adult_confirmed_at": timezone.now()},
        )
        changed: list[str] = []
        if user.display_name != display_name:
            user.display_name = display_name
            changed.append("display_name")
        if user.adult_confirmed_at is None:
            user.adult_confirmed_at = timezone.now()
            changed.append("adult_confirmed_at")
        if user.is_staff != is_staff:
            user.is_staff = is_staff
            changed.append("is_staff")
        if password:
            user.set_password(password)
            changed.append("password")
        elif created:
            user.set_unusable_password()
            changed.append("password")
        if changed:
            user.save(update_fields=changed)
        return user

    def _profile(
        self,
        *,
        user: User,
        name: str,
        slug: str,
        biography: str,
        languages: list[str],
    ) -> InstructorProfile:
        profile, _ = InstructorProfile.objects.update_or_create(
            user=user,
            defaults={
                "professional_name": name,
                "slug": slug,
                "biography": biography,
                "languages": languages,
                "remote_available": True,
                "is_published": True,
            },
        )
        return profile

    def _approved_link(self, *, owner: User, moderator: User, label: str, url: str) -> ExternalLink:
        link = ExternalLink.objects.filter(owner=owner, label=label).first()
        if link is None:
            link = ExternalLink.objects.create(owner=owner, label=label, url=url)
        elif link.url != url:
            link.url = url
            link.save(update_fields=["url"])
        link.approve(moderator=moderator)
        return link

    def _offer(
        self,
        *,
        instructor: InstructorProfile,
        link: ExternalLink,
        title: str,
        description: str,
        offer_format: str,
        price: str,
        reviews: int,
        turnaround: int,
        terms: str,
    ) -> MentoringOffer:
        offer, _ = MentoringOffer.objects.update_or_create(
            instructor=instructor,
            title=title,
            defaults={
                "description": description,
                "format": offer_format,
                "price_amount": price,
                "price_currency": "USD",
                "included_reviews": reviews,
                "turnaround_days": turnaround,
                "terms": terms,
                "booking_link": link,
                "is_active": True,
            },
        )
        return offer

    def _template(
        self,
        *,
        instructor: InstructorProfile,
        title: str,
        objective: str,
        instructions: str,
        criteria: str,
        minutes: int,
        page_slug: str,
        program: TrainingProgram | None = None,
    ) -> PracticeTemplate:
        practice, _ = PracticeTemplate.objects.update_or_create(
            instructor=instructor,
            title=title,
            defaults={
                "program": program,
                "objective": objective,
                "instructions": instructions,
                "evaluation_criteria": criteria,
                "estimated_minutes": minutes,
                "is_public": True,
            },
        )
        page = KnowledgePage.objects.filter(slug=page_slug).first()
        if page is not None:
            practice.linked_pages.add(page)
        return practice

    def _video(self, *, owner: User, identifier: str, description: str) -> VideoReference:
        video, _ = VideoReference.objects.update_or_create(
            owner=owner,
            provider=VideoReference.Provider.YOUTUBE,
            provider_id=identifier,
            defaults={
                "submitted_url": f"https://youtu.be/{identifier}",
                "attribution_name": f"{owner.display_name} · fictional demo",
                "description": description,
                "visibility": VideoReference.Visibility.UNLISTED,
            },
        )
        return video

    def _assignment(
        self,
        *,
        enrollment: Enrollment,
        template: PracticeTemplate,
        due_in_days: int,
        notes: str,
        status: str,
    ) -> PracticeAssignment:
        assignment, _ = PracticeAssignment.objects.update_or_create(
            enrollment=enrollment,
            template=template,
            defaults={
                "due_at": timezone.now() + timedelta(days=due_in_days),
                "personalized_notes": notes,
                "status": status,
            },
        )
        return assignment

    @transaction.atomic
    def handle(self, *args: object, **options: Any) -> None:
        mentor_password = str(options["mentor_password"])
        student_password = str(options["student_password"])
        moderator = self._user(
            email="demo-moderator@vdancehub.local",
            display_name="Demo Content Moderator",
            is_staff=True,
        )
        ana_user = self._user(
            email="demo-mentor@vdancehub.local",
            display_name="Ana Rivera",
            password=mentor_password,
        )
        mateo_user = self._user(email="demo-mateo@vdancehub.local", display_name="Mateo Cruz")
        priya_user = self._user(email="demo-priya@vdancehub.local", display_name="Priya Shah")
        kai = self._user(
            email="demo-student@vdancehub.local",
            display_name="Kai Morgan",
            password=student_password,
        )
        jules = self._user(email="demo-jules@vdancehub.local", display_name="Jules Lee")

        ana = self._profile(
            user=ana_user,
            name="Ana Rivera · Demo mentor",
            slug="demo-ana-rivera",
            biography=(
                "Fictional demo profile. Ana helps social Bachata dancers build clear rhythm, "
                "comfortable weight transfer, and responsive partner connection."
            ),
            languages=["English", "Spanish"],
        )
        mateo = self._profile(
            user=mateo_user,
            name="Mateo Cruz · Demo mentor",
            slug="demo-mateo-cruz",
            biography=(
                "Fictional demo profile. Mateo teaches linear Salsa with a practical focus on "
                "timing, cross-body lead technique, and confident social dancing."
            ),
            languages=["English", "Spanish", "Portuguese"],
        )
        priya = self._profile(
            user=priya_user,
            name="Priya Shah · Demo mentor",
            slug="demo-priya-shah",
            biography=(
                "Fictional demo profile. Priya coaches Casino and Rueda dancers in call timing, "
                "group awareness, partner changes, and joyful improvisation."
            ),
            languages=["English", "Hindi"],
        )

        links = {
            "ana_review": self._approved_link(
                owner=ana_user,
                moderator=moderator,
                label="Demo checkout · Ana video review",
                url="https://example.com/vdancehub-demo/ana/video-review",
            ),
            "ana_program": self._approved_link(
                owner=ana_user,
                moderator=moderator,
                label="Demo checkout · Ana mentorship",
                url="https://example.com/vdancehub-demo/ana/mentorship",
            ),
            "mateo": self._approved_link(
                owner=mateo_user,
                moderator=moderator,
                label="Demo checkout · Mateo video review",
                url="https://example.com/vdancehub-demo/mateo/review",
            ),
            "priya": self._approved_link(
                owner=priya_user,
                moderator=moderator,
                label="Demo checkout · Priya private lesson",
                url="https://example.com/vdancehub-demo/priya/lesson",
            ),
        }
        ana_review = self._offer(
            instructor=ana,
            link=links["ana_review"],
            title="One-time Bachata video review · Demo",
            description="A focused review with timestamped observations and one next exercise.",
            offer_format=MentoringOffer.Format.VIDEO_REVIEW,
            price="35.00",
            reviews=1,
            turnaround=4,
            terms="One fictional demo video up to two minutes. External payment is not real.",
        )
        self._offer(
            instructor=ana,
            link=links["ana_program"],
            title="Four-week Bachata foundations · Demo",
            description="Weekly practice, two detailed video reviews, and an evolving plan.",
            offer_format=MentoringOffer.Format.PROGRAM,
            price="120.00",
            reviews=2,
            turnaround=5,
            terms="Fictional four-week demo program. External payment is not real.",
        )
        self._offer(
            instructor=mateo,
            link=links["mateo"],
            title="Salsa technique review · Demo",
            description="A concise review of timing, pathway, frame, and lead clarity.",
            offer_format=MentoringOffer.Format.VIDEO_REVIEW,
            price="40.00",
            reviews=1,
            turnaround=3,
            terms="One fictional demo video up to 90 seconds.",
        )
        self._offer(
            instructor=priya,
            link=links["priya"],
            title="Private Casino coaching · Demo",
            description="A remote private lesson with a documented follow-up assignment.",
            offer_format=MentoringOffer.Format.PRIVATE_LESSON,
            price="55.00",
            reviews=1,
            turnaround=2,
            terms="Fictional 50-minute online lesson. Scheduling link is illustrative.",
        )

        curriculum = Curriculum.objects.filter(slug="rumba-y-timbal-bachata").first()
        program, _ = TrainingProgram.objects.update_or_create(
            instructor=ana,
            title="Four-week Bachata foundations · Demo",
            defaults={
                "curriculum": curriculum,
                "summary": "A fictional weekly pathway showing assignments and feedback history.",
                "is_published": True,
            },
        )
        week_one = self._template(
            instructor=ana,
            program=program,
            title="Week 1 · Rhythm and basic step",
            objective="Keep a steady Bachata rhythm with relaxed, complete steps.",
            instructions="Practice without music, then with one slow song. Record 30 seconds.",
            criteria="Timing, balance, continuity",
            minutes=12,
            page_slug="bachata-basic-step",
        )
        week_two = self._template(
            instructor=ana,
            program=program,
            title="Week 2 · Weight transfer",
            objective="Complete each weight transfer before beginning the next step.",
            instructions="Alternate side basics and forward-back basics for three short rounds.",
            criteria="Weight transfer, posture, rhythmic consistency",
            minutes=15,
            page_slug="bachata-basic-step",
        )
        week_three = self._template(
            instructor=ana,
            program=program,
            title="Week 3 · Partner connection",
            objective="Maintain comfortable connection while changing direction.",
            instructions="Practice the pathway solo, then with a partner if available.",
            criteria="Responsiveness, frame, shared timing",
            minutes=18,
            page_slug="partner-connection",
        )
        self._template(
            instructor=mateo,
            title="Cross-body lead pathway",
            objective="Create a clear pathway without rushing the follower.",
            instructions="Mark the pathway solo, then repeat with a partner at slow tempo.",
            criteria="Timing, slot awareness, invitation",
            minutes=15,
            page_slug="salsa-cross-body-lead",
        )
        self._template(
            instructor=mateo,
            title="Inside-turn preparation",
            objective="Prepare and complete an inside turn with consistent timing.",
            instructions="Practice preparation and release separately before combining them.",
            criteria="Preparation, hand path, balance",
            minutes=12,
            page_slug="salsa-cross-body-lead",
        )
        self._template(
            instructor=priya,
            title="Rueda call timing and awareness",
            objective="Respond to calls while preserving group spacing and shared rhythm.",
            instructions="Shadow five calls, naming the response and partner-change direction.",
            criteria="Call recognition, timing, group awareness",
            minutes=20,
            page_slug="partner-connection",
        )

        kai_enrollment, _ = Enrollment.objects.update_or_create(
            instructor=ana,
            student=kai,
            status__in=[Enrollment.Status.INVITED, Enrollment.Status.ACTIVE],
            defaults={"program": program, "status": Enrollment.Status.ACTIVE},
        )
        jules_enrollment, _ = Enrollment.objects.update_or_create(
            instructor=ana,
            student=jules,
            status__in=[Enrollment.Status.INVITED, Enrollment.Status.ACTIVE],
            defaults={"program": program, "status": Enrollment.Status.ACTIVE},
        )
        reviewed = self._assignment(
            enrollment=kai_enrollment,
            template=week_one,
            due_in_days=-10,
            notes="Start with comfort and consistency; do not make the step larger.",
            status=PracticeAssignment.Status.REVIEWED,
        )
        submitted = self._assignment(
            enrollment=kai_enrollment,
            template=week_two,
            due_in_days=1,
            notes="Pay attention to the right side, which felt less stable last week.",
            status=PracticeAssignment.Status.SUBMITTED,
        )
        self._assignment(
            enrollment=kai_enrollment,
            template=week_three,
            due_in_days=8,
            notes="Use solo practice if a partner is not available.",
            status=PracticeAssignment.Status.ASSIGNED,
        )

        first_video = self._video(
            owner=kai,
            identifier="VdanceDemo01",
            description="Fictional front-view demo submission for Week 1.",
        )
        first_submission, _ = PracticeSubmission.objects.update_or_create(
            assignment=reviewed,
            defaults={
                "student": kai,
                "video": first_video,
                "self_assessment": (
                    "The rhythm feels steadier. I still tense my shoulders when the music "
                    "speeds up."
                ),
            },
        )
        review, _ = InstructorReview.objects.update_or_create(
            submission=first_submission,
            defaults={
                "instructor": ana,
                "overall_feedback": (
                    "Your timing is much more consistent and your steps stay comfortably compact."
                ),
                "next_steps": (
                    "Keep the same step size and finish each weight transfer before the next count."
                ),
            },
        )
        ReviewAnnotation.objects.update_or_create(
            review=review,
            seconds=14,
            category=ReviewAnnotation.Category.TIMING,
            defaults={"body": "The rhythm settles here—keep this easy pace."},
        )
        ReviewAnnotation.objects.update_or_create(
            review=review,
            seconds=31,
            category=ReviewAnnotation.Category.BALANCE,
            defaults={"body": "Finish moving your weight before lifting the next foot."},
        )
        second_video = self._video(
            owner=kai,
            identifier="VdanceDemo02",
            description="Fictional side-view demo submission for Week 2.",
        )
        PracticeSubmission.objects.update_or_create(
            assignment=submitted,
            defaults={
                "student": kai,
                "video": second_video,
                "self_assessment": (
                    "The left side feels natural now. The right transfer is improving but still "
                    "needs conscious attention."
                ),
            },
        )

        MentoringRequest.objects.update_or_create(
            offer=ana_review,
            student=jules,
            status=MentoringRequest.Status.REQUESTED,
            defaults={
                "focus": (
                    "I would like help understanding why my basic step loses the beat during turns."
                )
            },
        )
        journal_seeds = (
            (14, 20, "Practiced the basic without music and noticed tension in my shoulders."),
            (7, 25, "Used one slow song. The rhythm felt easier after the first minute."),
            (0, 18, "Focused on completing the right-side weight transfer before the tap."),
        )
        for days_ago, minutes, notes in journal_seeds:
            PracticeJournal.objects.update_or_create(
                student=kai,
                practice_date=timezone.localdate() - timedelta(days=days_ago),
                defaults={"minutes": minutes, "notes": notes},
            )

        self.stdout.write(self.style.SUCCESS("Mentorship demo data is ready."))
        self.stdout.write("Mentor login: demo-mentor@vdancehub.local")
        self.stdout.write("Student login: demo-student@vdancehub.local")
        self.stdout.write("All people, offers, payments, and coaching records are fictional demos.")
