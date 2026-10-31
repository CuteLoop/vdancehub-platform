import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlsplit

from django.core.exceptions import ValidationError

YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{6,64}$")
INSTAGRAM_ID = re.compile(r"^[A-Za-z0-9_-]{5,64}$")
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com"}


@dataclass(frozen=True)
class ParsedVideoURL:
    provider: str
    provider_id: str
    canonical_url: str
    start_seconds: int | None = None


def _timestamp_seconds(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    if value.isdigit():
        return int(value)
    match = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", value)
    if not match or not any(match.groups()):
        raise ValidationError("Unsupported video timestamp.")
    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def parse_video_url(url: str) -> ParsedVideoURL:
    if not isinstance(url, str) or len(url) > 2048:
        raise ValidationError("Invalid video URL.")
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise ValidationError("Malformed video URL.") from exc
    if parts.scheme != "https" or not parts.hostname:
        raise ValidationError("Only HTTPS video URLs are accepted.")
    if parts.username or parts.password or port is not None:
        raise ValidationError("Credentials and explicit ports are not accepted.")
    try:
        hostname = parts.hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValidationError("Malformed video hostname.") from exc

    if hostname in YOUTUBE_HOSTS:
        return _parse_youtube(hostname, parts.path, parts.query)
    if hostname in INSTAGRAM_HOSTS:
        return _parse_instagram(parts.path)
    raise ValidationError("This video provider is not supported.")


def _parse_youtube(hostname: str, path: str, query: str) -> ParsedVideoURL:
    params = parse_qs(query, keep_blank_values=True)
    if hostname == "youtu.be":
        identifier = path.strip("/")
    elif path == "/watch":
        values = params.get("v", [])
        identifier = values[0] if len(values) == 1 else ""
    elif path.startswith("/shorts/"):
        pieces = path.strip("/").split("/")
        identifier = pieces[1] if len(pieces) == 2 else ""
    else:
        identifier = ""
    if not YOUTUBE_ID.fullmatch(identifier):
        raise ValidationError("Unsupported YouTube URL.")
    timestamp_values = params.get("t", []) or params.get("start", [])
    timestamp = _timestamp_seconds(timestamp_values[0]) if len(timestamp_values) == 1 else None
    return ParsedVideoURL(
        provider="youtube",
        provider_id=identifier,
        canonical_url=f"https://www.youtube.com/watch?v={identifier}",
        start_seconds=timestamp,
    )


def _parse_instagram(path: str) -> ParsedVideoURL:
    pieces = path.strip("/").split("/")
    if len(pieces) != 2 or pieces[0] not in {"p", "reel"}:
        raise ValidationError("Unsupported Instagram URL.")
    kind, identifier = pieces
    if not INSTAGRAM_ID.fullmatch(identifier):
        raise ValidationError("Unsupported Instagram URL.")
    return ParsedVideoURL(
        provider="instagram",
        provider_id=identifier,
        canonical_url=f"https://www.instagram.com/{kind}/{identifier}/",
    )
