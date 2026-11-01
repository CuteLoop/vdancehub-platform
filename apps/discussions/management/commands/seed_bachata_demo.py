from dataclasses import dataclass

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import User
from apps.discussions.models import DiscussionTopic
from apps.discussions.services import create_topic_with_first_post
from apps.knowledge.models import Movement, MovementRelationship, PostCitation, SourceReference
from apps.knowledge.references import classify_reference_url
from apps.taxonomy.models import DanceStyle, Tag


@dataclass(frozen=True)
class MoveSample:
    catalog_id: int
    title: str
    difficulty: int
    categories: tuple[str, ...]
    creator: str
    source_url: str = ""


CATALOG_URL = "https://bachatasteps.com/"
REDDIT_URL = "https://www.reddit.com/r/Bachata/comments/1bneys8/"
SAMPLES = (
    MoveSample(
        1783,
        "Cross Body Lead",
        1,
        ("footwork",),
        "Dance Dojo",
        "https://thedancedojo.com/modules/bachata-beginner-level-1/lessons/cross-body-open-1/",
    ),
    MoveSample(1600, "Diagonal MiniSteps", 1, ("footwork", "step"), "Imre"),
    MoveSample(1597, "Mambo Forward–Backward", 1, ("footwork", "mambo"), "Imre"),
    MoveSample(1596, "Late Footwork", 1, ("footwork",), "Imre"),
    MoveSample(1594, "Forward Step Variation", 1, ("footwork", "step"), "Imre"),
    MoveSample(1592, "Linea with Syncopation", 1, ("footwork",), "Imre"),
    MoveSample(
        1591,
        "Pico Pico – Forward & Back",
        1,
        ("footwork",),
        "Dima + Victoria",
        "https://www.instagram.com/p/DCjk-TgMBCa/?owner=dimayvictoria",
    ),
    MoveSample(
        1590,
        "Mambo Side-to-Side",
        1,
        ("footwork", "mambo"),
        "Dima + Victoria",
        "https://www.instagram.com/p/DCjk-TgMBCa/?owner=dimayvictoria",
    ),
    MoveSample(
        1589,
        "Flex Point – Heel Toe – Tap",
        1,
        ("footwork",),
        "Dima + Victoria",
        "https://www.instagram.com/p/DCjk-TgMBCa/?owner=dimayvictoria",
    ),
    MoveSample(
        5,
        "Barrel – One Hand",
        2,
        ("step",),
        "Harold + Regan",
        "https://www.youtube.com/watch?v=7Zi-aUnLrVk",
    ),
    MoveSample(7, "Hammerlock + Arm Drop + Turn Out", 2, ("partnerwork",), "Imre + Milena"),
    MoveSample(
        11,
        "One-Hand Hammerlock + Double Arm Circle",
        2,
        ("spectacular",),
        "Ataca + La Alemana",
        "https://www.youtube.com/watch?v=Bbrnmdkyk_s",
    ),
    MoveSample(
        12,
        "Turn + Sál + Pendulo",
        2,
        ("partnerwork",),
        "Unknown",
        "https://www.youtube.com/watch?v=4L9L7sE1inw",
    ),
    MoveSample(
        13,
        "Pretzel + Shadow + Arm Pattern",
        2,
        ("partnerwork",),
        "Unknown",
        "https://www.youtube.com/watch?v=4L9L7sE1inw",
    ),
    MoveSample(
        14,
        "Hammerlock + Sál + Underarm Pass",
        2,
        ("spectacular",),
        "Unknown",
        "https://www.youtube.com/watch?v=OBkmbACt1as",
    ),
    MoveSample(
        16,
        "Place Change + Armpit Hold + Head Roll",
        2,
        ("spectacular", "step"),
        "Unknown",
        "https://www.youtube.com/watch?v=rsSexvk0aIM",
    ),
    MoveSample(
        22,
        "Pretzel – Wave – Sit",
        2,
        ("sensual", "step"),
        "Marius + Elena",
        "https://mariuselena.com/",
    ),
    MoveSample(
        25,
        "Pretzel Underarm Push",
        2,
        ("sensual", "step"),
        "Marius + Elena",
        "https://www.youtube.com/watch?v=Io_o-9l_hUE&t=797",
    ),
    MoveSample(
        28,
        "Caricia + Spin + Arm Throw",
        2,
        ("partnerwork",),
        "Unknown",
        "https://www.facebook.com/watch/?v=1031977140940109",
    ),
    MoveSample(
        1,
        "Two-Hand Turn + Arm Throw + Caricia",
        3,
        ("partnerwork",),
        "Marius + Elena",
        "https://www.youtube.com/watch?v=hUBSMDeTG_E",
    ),
    MoveSample(
        3,
        "Two-Hand Turn + Arm Break + Arm Throw",
        3,
        ("partnerwork",),
        "Marius + Elena",
        "https://youtu.be/hUBSMDeTG_E?t=214",
    ),
    MoveSample(
        4,
        "Barrel – To Shoulder",
        3,
        ("step",),
        "Harold + Regan",
        "https://www.youtube.com/watch?v=7Zi-aUnLrVk",
    ),
    MoveSample(
        6,
        "Two-Hand Turn + Shoulder Changes + Pretzel",
        3,
        ("partnerwork",),
        "Unknown",
        "https://www.facebook.com/info.drsalsa",
    ),
    MoveSample(
        9,
        "Arm Throw + Outside Turn",
        3,
        ("partnerwork",),
        "Ataca + La Alemana",
        "https://www.youtube.com/watch?v=Bbrnmdkyk_s",
    ),
    MoveSample(
        19,
        "Turn + Armpit + Hand Change + Double Sál",
        3,
        ("partnerwork",),
        "Unknown",
        "https://www.youtube.com/watch?v=6jjdT4TklZk",
    ),
    MoveSample(
        20,
        "Place Change into Hammerlock",
        3,
        ("spectacular",),
        "Demetrio + Nicole",
        "https://youtu.be/H5WJhYHj3tM?t=63",
    ),
    MoveSample(
        1942, "Flower Fan", 3, ("lady-style",), "Brenda Liew", "https://brendaliewonline.com/"
    ),
    MoveSample(
        38,
        "Madrid Step + Shadow + Propeller Turn",
        4,
        ("spectacular", "step"),
        "Imre + Milena",
        "https://www.youtube.com/watch?v=HRhx99XpeLI",
    ),
    MoveSample(
        44,
        "Arm Circle + Arm Wave",
        4,
        ("sensual", "spectacular"),
        "VDanceClub",
        "https://vdanceclub.com/",
    ),
    MoveSample(
        54,
        "Hammerlock + Back-to-Back + Turn",
        4,
        ("spectacular",),
        "Ataca",
        "https://www.youtube.com/watch?v=-cTNIYSSXQ4",
    ),
    MoveSample(
        61,
        "Pendulo + Squat + Body Wave",
        4,
        ("spectacular", "sensual"),
        "Marius + Elena",
        "https://www.youtube.com/watch?v=Uoxp3r2iTeM&t=236",
    ),
    MoveSample(
        1952,
        "Crossing Side Wave + Underarm Duck + Rotation",
        4,
        ("sensual",),
        "Piotr + Dorota",
        "https://www.instagram.com/p/DPVrnf-DCJ1/",
    ),
    MoveSample(
        227,
        "Shadow Turn-Out + Place Change Sequence",
        5,
        ("partnerwork",),
        "Marius + Elena",
        "https://www.youtube.com/watch?v=Dvx71r7b4ZQ",
    ),
    MoveSample(
        333,
        "Advanced Sensual Combo",
        5,
        ("sensual",),
        "Unknown",
        "https://www.instagram.com/reel/CgKkhGvDrKR/",
    ),
    MoveSample(
        426,
        "Follower Side Raise with Leg",
        5,
        ("acrobatics", "spectacular"),
        "Simone + Danila",
        "https://www.tiktok.com/@simoneydanilabachata/video/7105453996827036933",
    ),
    MoveSample(
        499,
        "Turn + Dip + Belly Push",
        5,
        ("sensual", "spectacular"),
        "Jhair Bachata",
        "https://www.tiktok.com/@jhair.bachata12/video/7175196425905622278",
    ),
    MoveSample(
        585,
        "Cross-Handed Double-Around Cambré",
        5,
        ("sensual", "bachazouk", "spectacular"),
        "Unknown",
        "https://www.instagram.com/reel/CqGcJ2irCuh/",
    ),
)

CONCEPTS = (
    ("Basic Footwork", "basic-footwork", ("footwork",)),
    ("Mambo Footwork", "mambo-footwork", ("footwork", "mambo")),
    ("Turns", "turns", ("partnerwork",)),
    ("Hammerlock", "hammerlock", ("partnerwork",)),
    ("Arm Throw", "arm-throw", ("partnerwork",)),
    ("Pretzel", "pretzel", ("partnerwork",)),
    ("Shadow Position", "shadow-position", ("partnerwork",)),
    ("Body Wave", "body-wave", ("sensual",)),
    ("Caricia", "caricia", ("partnerwork",)),
    ("Dip and Cambré", "dip-cambre", ("sensual", "safety")),
)

COMPONENT_PATTERNS = {
    "footwork": "basic-footwork",
    "mambo": "mambo-footwork",
    "turn": "turns",
    "hammerlock": "hammerlock",
    "arm throw": "arm-throw",
    "pretzel": "pretzel",
    "shadow": "shadow-position",
    "wave": "body-wave",
    "caricia": "caricia",
    "dip": "dip-cambre",
    "cambr": "dip-cambre",
}


class Command(BaseCommand):
    help = "Create an attributed Bachata movement knowledge-graph demo."

    def _reference(
        self, *, url: str, title: str, attribution: str, curator: User
    ) -> SourceReference:
        classified = classify_reference_url(url)
        existing = SourceReference.objects.filter(
            canonical_url=classified.canonical_url, attribution_name=attribution
        ).first()
        if existing:
            existing.submitted_url = url
            existing.title = title
            existing.save()
            return existing
        return SourceReference.objects.create(
            submitted_url=url,
            title=title,
            attribution_name=attribution,
            added_by=curator,
        )

    def handle(self, *args: object, **options: object) -> None:
        curator, _ = User.objects.get_or_create(
            email="community-curator@vdancehub.local",
            defaults={
                "username": "vdancehub-curator",
                "display_name": "VDanceHub Curator",
                "adult_confirmed_at": timezone.now(),
            },
        )
        if curator.has_usable_password():
            curator.set_unusable_password()
            curator.save(update_fields=["password"])
        bachata, _ = DanceStyle.objects.get_or_create(name="Bachata", slug="bachata")
        move_tag, _ = Tag.objects.get_or_create(name="Move", slug="move")
        catalog_reference = self._reference(
            url=CATALOG_URL,
            title="BachataSteps community catalog",
            attribution="BachataSteps.com",
            curator=curator,
        )
        reddit_reference = self._reference(
            url=REDDIT_URL,
            title="Original r/Bachata project discussion",
            attribution="BachataSteps project author and r/Bachata contributors",
            curator=curator,
        )

        concepts: dict[str, Movement] = {}
        for name, slug, tag_slugs in CONCEPTS:
            concept, _ = Movement.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "dance_style": bachata,
                    "summary": (
                        "A normalized Bachata concept used to connect catalog movements. "
                        "Relationships remain proposals until community review."
                    ),
                    "is_concept": True,
                    "created_by": curator,
                },
            )
            for tag_slug in tag_slugs:
                tag, _ = Tag.objects.get_or_create(
                    name=tag_slug.replace("-", " ").title(), slug=tag_slug
                )
                concept.tags.add(tag)
            concepts[slug] = concept

        created_movements = 0
        for sample in SAMPLES:
            topic = DiscussionTopic.objects.filter(author=curator, title=sample.title).first()
            if topic is None:
                body = (
                    "Community catalog sample for terminology and technique discussion.\n\n"
                    f"Difficulty: {sample.difficulty} of 6\nCatalog ID: {sample.catalog_id}\n"
                    f"Attributed creator / demonstrator: {sample.creator}\n\n"
                    "Discussion prompts:\n"
                    "• What name does your school use for this movement?\n"
                    "• What prerequisite technique and safety notes matter?\n"
                    "• Is the catalog attribution or classification incomplete?\n\n"
                    "References are listed below as monitored, canonicalized citations."
                )
                thread_ref = create_topic_with_first_post(
                    author=curator,
                    title=sample.title,
                    kind=DiscussionTopic.Kind.RESOURCE,
                    body=body,
                )
                topic = thread_ref.native_topic
                assert topic is not None
            thread_ref = topic.domain_ref
            topic.dance_styles.add(bachata)
            topic.tags.add(move_tag)
            source_reference = catalog_reference
            if sample.source_url:
                source_reference = self._reference(
                    url=sample.source_url,
                    title=f"Creator source from {sample.creator}",
                    attribution=sample.creator,
                    curator=curator,
                )
            first_post = topic.posts.first()
            assert first_post is not None
            references = [source_reference]
            if catalog_reference.pk != source_reference.pk:
                references.append(catalog_reference)
            references.append(reddit_reference)
            for position, reference in enumerate(references, start=1):
                PostCitation.objects.get_or_create(
                    post=first_post,
                    position=position,
                    defaults={"reference": reference},
                )

            movement, created = Movement.objects.get_or_create(
                source_catalog="BachataSteps",
                source_identifier=str(sample.catalog_id),
                defaults={
                    "name": sample.title,
                    "slug": f"{slugify(sample.title)}-{sample.catalog_id}",
                    "dance_style": bachata,
                    "summary": (
                        f"A level {sample.difficulty} catalog movement attributed to "
                        f"{sample.creator}. Naming and graph relationships are open to review."
                    ),
                    "difficulty": sample.difficulty,
                    "discussion": thread_ref,
                    "created_by": curator,
                },
            )
            if movement.discussion_id is None:
                movement.discussion = thread_ref
                movement.save(update_fields=["discussion", "updated_at"])
            movement.references.add(source_reference, catalog_reference, reddit_reference)
            movement.tags.add(move_tag)
            for tag_slug in sample.categories:
                tag, _ = Tag.objects.get_or_create(
                    name=tag_slug.replace("-", " ").title(), slug=tag_slug
                )
                movement.tags.add(tag)
            created_movements += int(created)

            normalized_name = sample.title.lower()
            if "footwork" in sample.categories:
                normalized_name += " footwork"
            for pattern, concept_slug in COMPONENT_PATTERNS.items():
                if pattern in normalized_name:
                    MovementRelationship.objects.get_or_create(
                        from_movement=movement,
                        to_movement=concepts[concept_slug],
                        kind=MovementRelationship.Kind.COMPONENT,
                        defaults={
                            "status": MovementRelationship.Status.PROPOSED,
                            "provenance": MovementRelationship.Provenance.INFERRED,
                            "note": f"Suggested because the imported name contains “{pattern}”.",
                            "created_by": curator,
                        },
                    )

        for concept_slug, prerequisite_slug in (
            ("mambo-footwork", "basic-footwork"),
            ("hammerlock", "turns"),
        ):
            MovementRelationship.objects.get_or_create(
                from_movement=concepts[concept_slug],
                to_movement=concepts[prerequisite_slug],
                kind=MovementRelationship.Kind.PREREQUISITE,
                defaults={
                    "status": MovementRelationship.Status.PROPOSED,
                    "provenance": MovementRelationship.Provenance.CURATED,
                    "note": "Proposed learning progression; requires community review.",
                    "created_by": curator,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Knowledge graph ready: {len(SAMPLES)} catalog movements; "
                f"{created_movements} newly created."
            )
        )
