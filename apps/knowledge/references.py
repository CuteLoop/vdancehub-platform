from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.core.exceptions import ValidationError

from apps.mediarefs.parsers import INSTAGRAM_HOSTS, YOUTUBE_HOSTS, parse_video_url
from apps.mentoring.validators import validate_external_https_url

DOMAIN_ALLOWLIST = {
    "bachatasteps.com",
    "www.bachatasteps.com",
    "thedancedojo.com",
    "www.thedancedojo.com",
    "mariuselena.com",
    "www.mariuselena.com",
    "reddit.com",
    "www.reddit.com",
    "rumbaytimbal.com",
    "www.rumbaytimbal.com",
    "casinorueda.mit.edu",
    "vdanceclub.com",
    "www.vdanceclub.com",
}
TRACKING_PARAMETERS = {"fbclid", "gclid", "si", "owner"}


@dataclass(frozen=True)
class ClassifiedReference:
    provider: str
    canonical_url: str
    hostname: str
    validation_status: str


def classify_reference_url(url: str) -> ClassifiedReference:
    if not isinstance(url, str) or len(url) > 2048:
        raise ValidationError("Invalid reference URL.")
    validate_external_https_url(url)
    parts = urlsplit(url)
    assert parts.hostname is not None
    hostname = parts.hostname.encode("idna").decode("ascii").lower()

    if hostname in YOUTUBE_HOSTS | INSTAGRAM_HOSTS:
        parsed = parse_video_url(url)
        return ClassifiedReference(
            provider=parsed.provider,
            canonical_url=parsed.canonical_url,
            hostname=urlsplit(parsed.canonical_url).hostname or hostname,
            validation_status="domain_validated",
        )
    if any(provider_host in hostname for provider_host in YOUTUBE_HOSTS | INSTAGRAM_HOSTS):
        raise ValidationError("Deceptive provider hostname.")

    filtered_query = urlencode(
        [
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMETERS
        ],
        doseq=True,
    )
    canonical_url = urlunsplit(("https", hostname, parts.path or "/", filtered_query, ""))
    status = "domain_validated" if hostname in DOMAIN_ALLOWLIST else "unreviewed"
    return ClassifiedReference(
        provider="website",
        canonical_url=canonical_url,
        hostname=hostname,
        validation_status=status,
    )
