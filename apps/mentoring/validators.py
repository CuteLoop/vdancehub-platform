import ipaddress
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError


def validate_external_https_url(url: str) -> None:
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise ValidationError("Malformed external URL.") from exc
    if parts.scheme != "https" or not parts.hostname:
        raise ValidationError("External links must use HTTPS.")
    if parts.username or parts.password or port is not None:
        raise ValidationError("Credentials and explicit ports are not accepted.")
    try:
        hostname = parts.hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValidationError("Malformed external hostname.") from exc
    if hostname == "localhost" or hostname.endswith(".local"):
        raise ValidationError("Local destinations are not accepted.")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return
    if not address.is_global:
        raise ValidationError("Private or reserved network destinations are not accepted.")
