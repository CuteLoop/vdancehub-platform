from dataclasses import dataclass

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.discussions.models import DiscussionTopic
from apps.discussions.services import create_topic_with_first_post
from apps.knowledge.models import (
    Curriculum,
    CurriculumModule,
    CurriculumVersion,
    ModuleConcept,
    Movement,
    MovementRelationship,
    PostCitation,
    SourceReference,
)
from apps.knowledge.references import classify_reference_url
from apps.taxonomy.models import DanceStyle, Tag


@dataclass(frozen=True)
class ModuleSeed:
    title: str
    summary: str
    concepts: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class CurriculumSeed:
    name: str
    slug: str
    style_name: str
    style_slug: str
    organization: str
    summary: str
    source_url: str
    modules: tuple[ModuleSeed, ...]


SHARED_CONNECTION = ("Partner connection", "shared-partner-connection")

CURRICULA = (
    CurriculumSeed(
        name="Bachata social dancing",
        slug="rumba-y-timbal-bachata",
        style_name="Bachata",
        style_slug="bachata",
        organization="Rumba y Timbal Dance Studio",
        summary=(
            "A social-dance pathway from foundational rhythm and steps into turns, "
            "footwork, connection, and progressive partnerwork."
        ),
        source_url="https://www.rumbaytimbal.com/rumba-video-library/",
        modules=(
            ModuleSeed(
                "Beginner",
                "Foundational steps, rhythm, posture, connection, and first turns.",
                (
                    ("Basic step", "bachata-basic-step"),
                    ("Side step", "bachata-side-step"),
                    ("Back and forward basic", "bachata-back-forward-basic"),
                    ("Box step", "bachata-box-step"),
                    ("Weight transfer", "bachata-weight-transfer"),
                    ("Rhythm", "bachata-rhythm"),
                    ("Frame", "bachata-frame"),
                    SHARED_CONNECTION,
                    ("Half turn", "bachata-half-turn"),
                    ("Left and right turns", "bachata-left-right-turns"),
                ),
            ),
            ModuleSeed(
                "Advanced Beginner",
                "More intricate footwork, prepared turns, partner positions, and transitions.",
                (
                    ("Angle basic", "bachata-angle-basic"),
                    ("Cruzados", "bachata-cruzados"),
                    ("Delay turn", "bachata-delay-turn"),
                    ("Double right and left turn", "bachata-double-turn"),
                    ("Half grapevine", "bachata-half-grapevine"),
                    ("Prepared turn", "bachata-prepared-turn"),
                    ("Closed cuddle", "bachata-closed-cuddle"),
                    ("Hammerlock", "bachata-curriculum-hammerlock"),
                    ("Open cuddle", "bachata-open-cuddle"),
                    ("Rompe", "bachata-rompe"),
                ),
            ),
        ),
    ),
    CurriculumSeed(
        name="Linear Salsa",
        slug="rumba-y-timbal-linear-salsa",
        style_name="Linear Salsa",
        style_slug="linear-salsa",
        organization="Rumba y Timbal Dance Studio",
        summary=(
            "A linear salsa progression connecting solo steps, cross-body lead mechanics, "
            "turn families, shines, and partnerwork."
        ),
        source_url="https://www.rumbaytimbal.com/rumba-video-library/",
        modules=(
            ModuleSeed(
                "Beginner",
                "Basic rhythm and posture expressed through solo steps and partnerwork.",
                (
                    ("Basic step", "salsa-basic-step"),
                    ("Side step", "salsa-side-step"),
                    ("Back step", "salsa-back-step"),
                    ("Half and half", "salsa-half-and-half"),
                    ("Hesitation left", "salsa-hesitation-left"),
                    ("Suzy Q", "salsa-suzy-q"),
                    SHARED_CONNECTION,
                    ("Cross-body lead", "salsa-cross-body-lead"),
                    ("Right turn", "salsa-right-turn"),
                ),
            ),
            ModuleSeed(
                "Advanced Beginner",
                "Turn variations, copa, refined back-step technique, and handhold changes.",
                (
                    ("Angle Suzy Q", "salsa-angle-suzy-q"),
                    ("Cross-cross Suzy Q", "salsa-cross-cross-suzy-q"),
                    ("Double Suzy Q", "salsa-double-suzy-q"),
                    ("Mambo seco", "salsa-mambo-seco"),
                    ("Inside turn", "salsa-inside-turn"),
                    ("Outside turn", "salsa-outside-turn"),
                    ("Copa", "salsa-copa"),
                    ("Hook turn", "salsa-hook-turn"),
                    ("Hammerlock", "salsa-hammerlock"),
                    ("Pass through", "salsa-pass-through"),
                ),
            ),
        ),
    ),
    CurriculumSeed(
        name="MIT Casino Rueda",
        slug="mit-casino-rueda",
        style_name="Casino / Rueda",
        style_slug="casino-rueda",
        organization="MIT Casino Rueda",
        summary=(
            "A modular pathway built around named calls, movement families, partner changes, "
            "and group coordination."
        ),
        source_url="https://casinorueda.mit.edu/syllabus/",
        modules=(
            ModuleSeed(
                "Level 1 · Open module",
                "An independent introduction to open-position basics and calls.",
                (
                    ("Guapea", "casino-guapea"),
                    ("Call timing", "casino-call-timing"),
                    ("Dame directo", "casino-dame-directo"),
                    ("Enchufla y quédate", "casino-enchufla-quedate"),
                ),
            ),
            ModuleSeed(
                "Level 1 · Closed module",
                "An independent introduction to son basics, closed calls, and partner changes.",
                (
                    ("Son basic", "casino-son-basic"),
                    ("Se viró", "casino-se-viro"),
                    ("Tarros", "casino-tarros"),
                    ("Adiós", "casino-adios"),
                ),
            ),
            ModuleSeed(
                "Level 2 · Dame",
                "Partner changes, consecutive calls, and the Dame family.",
                (
                    ("Dame", "casino-dame"),
                    ("Dame dos", "casino-dame-dos"),
                    ("Pa'rriba", "casino-parriba"),
                    ("Espresso", "casino-espresso"),
                    ("Partner change", "casino-partner-change"),
                ),
            ),
            ModuleSeed(
                "Level 2 · Enchufla",
                "Walking turns and the Enchufla family in consecutive calls.",
                (
                    ("Enchufla", "casino-enchufla"),
                    ("Pa ti pa mí", "casino-pa-ti-pa-mi"),
                    ("Enchufla complicado", "casino-enchufla-complicado"),
                    ("Festival de pelotas", "casino-festival-pelotas"),
                    ("Festival de enchuflas", "casino-festival-enchuflas"),
                ),
            ),
            ModuleSeed(
                "Level 2 · Adiós",
                "Hook turns, partner changes, and the extended Adiós family.",
                (
                    ("Adiós largo", "casino-adios-largo"),
                    ("Adiós con la hermana", "casino-adios-hermana"),
                    ("Adiós con la familia", "casino-adios-familia"),
                    ("Evelyn", "casino-evelyn"),
                    ("Hook turn", "casino-hook-turn"),
                ),
            ),
            ModuleSeed(
                "Level 2 · Exhíbela",
                "Presentation calls and consecutive movement choices.",
                (
                    ("Aguajea", "casino-aguajea"),
                    ("Exhíbela", "casino-exhibela"),
                    ("Flamenco", "casino-flamenco"),
                    ("Americano and americana", "casino-americano-americana"),
                    ("Consecutive moves", "casino-consecutive-moves"),
                ),
            ),
        ),
    ),
)

REDDIT_URL = "https://www.reddit.com/r/Bachata/comments/1igk3vo/"


class Command(BaseCommand):
    help = "Create three attributed curriculum pilots in one shared knowledge graph."

    def _reference(
        self, *, url: str, title: str, attribution: str, curator: User
    ) -> SourceReference:
        classified = classify_reference_url(url)
        reference = SourceReference.objects.filter(
            canonical_url=classified.canonical_url, attribution_name=attribution
        ).first()
        if reference is not None:
            return reference
        return SourceReference.objects.create(
            submitted_url=url,
            title=title,
            attribution_name=attribution,
            added_by=curator,
        )

    def handle(self, *args: object, **options: object) -> None:
        curator, _ = User.objects.get_or_create(
            email="curriculum-curator@vdancehub.local",
            defaults={
                "username": "curriculum-curator",
                "display_name": "VDanceHub Curriculum Curator",
                "adult_confirmed_at": timezone.now(),
            },
        )
        if curator.has_usable_password():
            curator.set_unusable_password()
            curator.save(update_fields=["password"])

        cross_style, _ = DanceStyle.objects.get_or_create(
            name="Cross-style principle", slug="cross-style"
        )
        concept_tag, _ = Tag.objects.get_or_create(name="Curriculum concept", slug="curriculum")
        reddit = self._reference(
            url=REDDIT_URL,
            title="Community discussion about Bachata syllabus design",
            attribution="r/Bachata contributors",
            curator=curator,
        )

        for curriculum_seed in CURRICULA:
            style, _ = DanceStyle.objects.get_or_create(
                name=curriculum_seed.style_name, slug=curriculum_seed.style_slug
            )
            source = self._reference(
                url=curriculum_seed.source_url,
                title=f"Published syllabus for {curriculum_seed.name}",
                attribution=curriculum_seed.organization,
                curator=curator,
            )
            topic = DiscussionTopic.objects.filter(
                author=curator, title=f"Review: {curriculum_seed.name}"
            ).first()
            if topic is None:
                thread = create_topic_with_first_post(
                    author=curator,
                    title=f"Review: {curriculum_seed.name}",
                    kind=DiscussionTopic.Kind.DISCUSSION,
                    body=(
                        "Which fundamentals are missing? Which skills should be prerequisites, "
                        "and does this progression match real social-dancing experience?\n\n"
                        "The curriculum titles are attributed to the linked publisher. Graph edges "
                        "are community-reviewable proposals, not universal teaching facts."
                    ),
                )
                topic = thread.native_topic
                assert topic is not None
            thread = topic.domain_ref
            topic.dance_styles.add(style)
            first_post = topic.posts.first()
            assert first_post is not None
            PostCitation.objects.get_or_create(
                post=first_post, position=1, defaults={"reference": source}
            )
            if curriculum_seed.style_slug == "bachata":
                PostCitation.objects.get_or_create(
                    post=first_post, position=2, defaults={"reference": reddit}
                )

            curriculum, _ = Curriculum.objects.update_or_create(
                slug=curriculum_seed.slug,
                defaults={
                    "name": curriculum_seed.name,
                    "dance_style": style,
                    "organization": curriculum_seed.organization,
                    "summary": curriculum_seed.summary,
                    "source": source,
                    "discussion": thread,
                    "created_by": curator,
                },
            )
            version, _ = CurriculumVersion.objects.get_or_create(
                curriculum=curriculum,
                label="Pilot source snapshot · 2026-11-01",
                defaults={
                    "status": CurriculumVersion.Status.PUBLISHED,
                    "note": "Concise titles and ordering imported with attribution.",
                },
            )

            for module_position, module_seed in enumerate(curriculum_seed.modules, start=1):
                module, _ = CurriculumModule.objects.update_or_create(
                    version=version,
                    slug=f"module-{module_position}",
                    defaults={
                        "title": module_seed.title,
                        "summary": module_seed.summary,
                        "position": module_position,
                    },
                )
                previous: Movement | None = None
                for concept_position, (name, slug) in enumerate(module_seed.concepts, start=1):
                    concept_style = cross_style if slug == SHARED_CONNECTION[1] else style
                    concept, _ = Movement.objects.update_or_create(
                        slug=slug,
                        defaults={
                            "name": name,
                            "dance_style": concept_style,
                            "summary": (
                                f"A curriculum concept appearing in {curriculum_seed.name}. "
                                "Technique details and cross-style equivalence remain open "
                                "to review."
                            ),
                            "is_concept": True,
                            "created_by": curator,
                        },
                    )
                    concept.tags.add(concept_tag)
                    ModuleConcept.objects.update_or_create(
                        module=module,
                        concept=concept,
                        defaults={
                            "position": concept_position,
                            "source": source,
                            "note": "Taught in this published curriculum module.",
                        },
                    )
                    if previous is not None:
                        MovementRelationship.objects.get_or_create(
                            from_movement=concept,
                            to_movement=previous,
                            kind=MovementRelationship.Kind.PREREQUISITE,
                            defaults={
                                "status": MovementRelationship.Status.PROPOSED,
                                "provenance": MovementRelationship.Provenance.IMPORTED,
                                "note": (
                                    "Proposed from source ordering; this is not an asserted "
                                    "universal prerequisite."
                                ),
                                "created_by": curator,
                            },
                        )
                    previous = concept

        self.stdout.write(
            self.style.SUCCESS(
                f"Curriculum graph ready: {Curriculum.objects.count()} curricula, "
                f"{CurriculumModule.objects.count()} modules, "
                f"{ModuleConcept.objects.count()} module concepts."
            )
        )
