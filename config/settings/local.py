import os

from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-development-only")
ALLOWED_HOSTS = [
    host for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host
]
CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin
]
if os.getenv("TRUST_PROXY_SSL") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Development servers should serve source static assets directly. Production
# keeps the compressed manifest backend configured in production.py.
STORAGES = {  # noqa: F405
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
