import pytest
from django.core.exceptions import ValidationError

from apps.mediarefs.parsers import parse_video_url


@pytest.mark.parametrize(
    ("url", "provider", "identifier", "canonical", "start"),
    [
        (
            "https://www.youtube.com/watch?v=abc_DEF-12x&utm_source=test&t=1m30s",
            "youtube",
            "abc_DEF-12x",
            "https://www.youtube.com/watch?v=abc_DEF-12x",
            90,
        ),
        (
            "https://youtu.be/abc_DEF-12x?si=tracking",
            "youtube",
            "abc_DEF-12x",
            "https://www.youtube.com/watch?v=abc_DEF-12x",
            None,
        ),
        (
            "https://www.youtube.com/shorts/abc_DEF-12x",
            "youtube",
            "abc_DEF-12x",
            "https://www.youtube.com/watch?v=abc_DEF-12x",
            None,
        ),
        (
            "https://www.instagram.com/reel/ABC_def12/?utm_source=test",
            "instagram",
            "ABC_def12",
            "https://www.instagram.com/reel/ABC_def12/",
            None,
        ),
    ],
)
def test_parse_and_canonicalize_supported_video_urls(
    url: str, provider: str, identifier: str, canonical: str, start: int | None
) -> None:
    parsed = parse_video_url(url)
    assert parsed.provider == provider
    assert parsed.provider_id == identifier
    assert parsed.canonical_url == canonical
    assert parsed.start_seconds == start


@pytest.mark.parametrize(
    "url",
    [
        "http://youtube.com/watch?v=abc_DEF-12x",
        "javascript:alert(1)",
        "https://youtube.com.evil.example/watch?v=abc_DEF-12x",
        "https://youtube.com@evil.example/watch?v=abc_DEF-12x",
        "https://user:pass@youtube.com/watch?v=abc_DEF-12x",
        "https://youtube.com:443/watch?v=abc_DEF-12x",
        "https://youtube.com/watch?v=",
        "https://youtube.com/embed/abc_DEF-12x",
        "https://instagram.com.evil.example/reel/ABC_def12/",
        "https://instagram.com/explore/ABC_def12/",
        "<iframe src='https://youtube.com/watch?v=abc_DEF-12x'></iframe>",
    ],
)
def test_rejects_unsafe_or_unsupported_urls(url: str) -> None:
    with pytest.raises(ValidationError):
        parse_video_url(url)
