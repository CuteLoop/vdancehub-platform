FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY pyproject.toml README.md ./
COPY apps ./apps
COPY config ./config
COPY manage.py ./
RUN python -m pip install .
COPY templates ./templates
COPY static ./static
RUN DJANGO_SETTINGS_MODULE=config.settings.test python manage.py collectstatic --noinput
USER app
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]

