from dataclasses import dataclass

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.discussions.models import DiscussionTopic
from apps.discussions.services import create_topic_with_first_post
from apps.taxonomy.models import DanceStyle, Tag


@dataclass(frozen=True)
class MoveSample:
    catalog_id: int
    title: str
    creator: str
    source_url: str
    tags: tuple[str, ...]


CATALOG_URL = "https://bachatasteps.com/"
REDDIT_URL = "https://www.reddit.com/r/Bachata/comments/1bneys8/"
SAMPLES = (
    MoveSample(
        1783,
        "Cross Body Lead",
        "Dance Dojo",
        "https://thedancedojo.com/modules/bachata-beginner-level-1/lessons/cross-body-open-1/",
        ("move", "footwork", "beginner"),
    ),
    MoveSample(
        1600,
        "Diagonal MiniSteps",
        "Imre / BachataSteps community catalog",
        CATALOG_URL,
        ("move", "footwork", "beginner"),
    ),
    MoveSample(
        1597,
        "Mambo Forward–Backward",
        "Imre / BachataSteps community catalog",
        CATALOG_URL,
        ("move", "footwork", "beginner", "mambo"),
    ),
    MoveSample(
        1591,
        "Pico Pico – Forward & Back",
        "Dima + Victoria",
        "https://www.instagram.com/p/DCjk-TgMBCa/",
        ("move", "footwork", "beginner"),
    ),
    MoveSample(
        1590,
        "Mambo Side-to-Side",
        "Dima + Victoria",
        "https://www.instagram.com/p/DCjk-TgMBCa/",
        ("move", "footwork", "beginner", "mambo"),
    ),
)


class Command(BaseCommand):
    help = "Create an attributed five-topic Bachata discussion demo."

    def handle(self, *args: object, **options: object) -> None:
        curator, _ = User.objects.get_or_create(
            email="community-curator@vdancehub.local",
            defaults={
                "username": "vdancehub-curator",
                "display_name": "VDanceHub Curator",
                "adult_confirmed_at": timezone.now(),
            },
        )
        if not curator.has_usable_password():
            pass
        else:
            curator.set_unusable_password()
            curator.save(update_fields=["password"])
        bachata, _ = DanceStyle.objects.get_or_create(name="Bachata", slug="bachata")

        created_count = 0
        for sample in SAMPLES:
            existing = DiscussionTopic.objects.filter(author=curator, title=sample.title).first()
            if existing is not None:
                continue
            body = (
                "Community catalog sample for terminology and technique discussion.\n\n"
                f"Difficulty: 1 of 6\nCatalog ID: {sample.catalog_id}\n"
                f"Attributed creator / demonstrator: {sample.creator}\n"
                f"Original creator source: {sample.source_url}\n"
                f"Catalog: BachataSteps.com — {CATALOG_URL}\n"
                f"Reddit project discussion: {REDDIT_URL}\n\n"
                "Discussion prompts:\n"
                "• What name does your school use for this movement?\n"
                "• What prerequisite technique and safety notes matter?\n"
                "• Is the catalog attribution or classification incomplete?\n\n"
                "VDanceHub stores only this small attributed metadata sample and outbound links; "
                "it does not copy or host the source video."
            )
            thread_ref = create_topic_with_first_post(
                author=curator,
                title=sample.title,
                kind=DiscussionTopic.Kind.RESOURCE,
                body=body,
            )
            topic = thread_ref.native_topic
            assert topic is not None
            topic.dance_styles.add(bachata)
            for slug in sample.tags:
                tag, _ = Tag.objects.get_or_create(name=slug.replace("-", " ").title(), slug=slug)
                topic.tags.add(tag)
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created_count} Bachata demo topics."))
