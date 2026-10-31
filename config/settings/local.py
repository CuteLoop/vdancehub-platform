import os

from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-development-only")
ALLOWED_HOSTS = [
    host for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host
]
