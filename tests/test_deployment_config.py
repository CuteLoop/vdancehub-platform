from pathlib import Path


def test_docker_image_builds_production_static_manifest():
    dockerfile = Path("Dockerfile").read_text()

    assert (
        "DJANGO_SETTINGS_MODULE=config.settings.base python manage.py collectstatic" in dockerfile
    )


def test_docker_startup_applies_pending_migrations():
    dockerfile = Path("Dockerfile").read_text()

    assert "python manage.py migrate --noinput &&" in dockerfile
