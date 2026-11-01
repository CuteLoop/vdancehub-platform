from apps.accounts.models import User

from .models import PostCitation, SourceReference
from .references import classify_reference_url


def attach_post_references(*, post: object, urls: list[str], author: User) -> None:
    from apps.discussions.models import DiscussionPost

    assert isinstance(post, DiscussionPost)
    for position, url in enumerate(urls, start=1):
        classified = classify_reference_url(url)
        reference = SourceReference.objects.filter(
            canonical_url=classified.canonical_url,
            attribution_name=author.display_name,
        ).first()
        if reference is None:
            reference = SourceReference.objects.create(
                submitted_url=url,
                title=f"Reference from {author.display_name}",
                attribution_name=author.display_name,
                added_by=author,
            )
        PostCitation.objects.create(post=post, reference=reference, position=position)
