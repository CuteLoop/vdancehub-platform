import importlib


def test_production_errors_are_logged_to_console(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret-key-for-settings-import")
    monkeypatch.setenv("ALLOWED_HOSTS", "example.com")
    monkeypatch.setenv("DATABASE_URL", "sqlite:////tmp/vdancehub-production-settings.sqlite3")
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")

    production = importlib.import_module("config.settings.production")

    assert production.LOGGING["handlers"]["console"]["class"] == "logging.StreamHandler"
    assert "console" in production.LOGGING["loggers"]["django.request"]["handlers"]
