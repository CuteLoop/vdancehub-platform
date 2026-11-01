# VDanceHub Codex project instructions

## Product boundary

VDanceHub is an adult-only collaborative dance commons. It connects discussions, structured
movement knowledge, feedback, projects, communities, and instructor-owned mentoring links.

## Engineering workflow

- Use test-driven development: write or update a failing test before behavior changes.
- Run `pytest`, Ruff, strict mypy, and the migration drift check before committing.
- Keep the Django modular monolith and PostgreSQL-compatible ORM models.
- Preserve upstream attribution and provenance. Imported relationships are proposals, not facts.
- Never copy or host third-party dance videos in the MVP.
- Never fetch user-submitted URLs server-side or render submitted HTML/embed code.
- Validate external URLs with parsed scheme, hostname, port, credentials, and provider paths.
- Keep arbitrary external links unclickable until a moderator reviews them.
- Render user-generated links with `rel="noopener noreferrer nofollow ugc"`.
- Preserve object-level permissions, adult confirmation, moderation, reporting, and consent checks.

## Common commands

```bash
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy apps config
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py check --deploy --settings=config.settings.production
```

The optional local knowledge demo is seeded explicitly with:

```bash
.venv/bin/python manage.py seed_bachata_demo
```
