# VDanceHub Platform

VDanceHub is a collaborative dance commons: an accessible discussion space, a structured
knowledge base, and a path to professional mentorship. It is intentionally organized around
purposeful discovery rather than an endless feed.

The product has six connected activities: **Discuss**, **Get Feedback**, **Explore**, **Find
Mentors**, **Collaborate**, and **Find Community**. The defining alpha journey is documented in
[the product specification](docs/product/product-spec.md).

> **Project status:** pre-alpha. The data model and security-critical URL parser are under active
> development. Do not deploy this repository as a public service yet.

## Technical direction

- Django 5.2 modular monolith and PostgreSQL 16
- Django templates, Bootstrap 5, and selective HTMX enhancement
- External YouTube and Instagram references; no uploaded video or arbitrary embed HTML
- PostgreSQL search; no recommendation feed
- Instructor-owned, moderator-reviewed external booking links; no platform payments
- Test-driven development with pytest

See [architecture](docs/architecture/architecture.md), [security and privacy](docs/security/threat-model.md),
the [delivery plan](docs/delivery/implementation-plan.md), the current
[MVP progress audit](docs/delivery/progress-audit.md), and the demo import
[data provenance](docs/data-provenance.md).

The knowledge experience follows the [living knowledge commons principles](docs/product/knowledge-commons-principles.md):
open discussions feed collaboratively maintained pages, while scoped reviewed editions preserve
stable snapshots without claiming universal authority.

## Local development

Prerequisites: Python 3.12+ (production target: 3.13), Docker, and Docker Compose.

```bash
cp .env.example .env
docker compose up -d db redis
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python manage.py migrate
.venv/bin/pytest
```

The health endpoint is `http://localhost:8000/health/` after running
`.venv/bin/python manage.py runserver`.

To load the bounded Bachata knowledge demonstration, run:

```bash
.venv/bin/python manage.py seed_bachata_demo
```

Then open `http://localhost:8000/knowledge/moves/`. The seed creates 37 attributed catalog
records, ten normalized concepts, linked discussions, and proposed relationships for community
review. See the [data provenance notes](docs/data-provenance.md) before expanding the import.

To load the three-curriculum pilot and shared concept graph, run:

```bash
.venv/bin/python manage.py seed_curriculum_pilot
```

Then open `http://localhost:8000/knowledge/curricula/` or
`http://localhost:8000/knowledge/graph/`. The pilot keeps the two Rumba y Timbal pathways and MIT's
modular Casino/Rueda pathway distinct while allowing concepts to participate in one attributed,
community-reviewable graph.

To load a fictional end-to-end mentorship workflow, run:

```bash
.venv/bin/python manage.py seed_mentoring_demo \
  --mentor-password '<temporary-demo-password>' \
  --student-password '<temporary-demo-password>'
```

The idempotent seed creates clearly labeled demo mentors, offers, a program, assignments in each
workflow state, submissions, timestamped feedback, a pending request, and a personal practice
journal. Open `/mentoring/` for discovery, then use the two demo accounts printed by the command.

## Safety boundary

The alpha is for adults aged 18 and over. Feedback videos are unlisted by default, but “unlisted”
is link privacy—not secure private storage. Submitters must have permission from every identifiable
participant. Read the full policy before implementing public submission flows.

## License

Copyright © 2026 VDanceHub contributors. Licensed under the GNU Affero General Public License,
version 3 or later.

