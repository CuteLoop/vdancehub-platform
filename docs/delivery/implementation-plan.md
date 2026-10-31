# TDD implementation plan

Codex is the main implementer. Work in small behavior-focused branches and use red-green-refactor:
first add a failing test, implement the smallest passing behavior, then refactor without weakening the
assertion. Every pull request identifies permission/threat impact, migrations, tests, and rollback.

## Milestones

1. **Foundation:** repository, governance, settings, Docker, CI, custom user, docs, health check.
2. **Forum spike and safety:** contract tests, Spirit decision, taxonomy, communities, reporting,
   blocking, moderation, and rate limiting.
3. **Feedback vertical:** URL parser, reusable video model, visibility, consent, requests, timestamped
   replies, reporting, withdrawal, and safe display adapters.
4. **Mentoring:** profiles, offers, search filters, reviewed outbound links, and disclaimers.
5. **Knowledge/projects:** contributor permissions, revisions, references, milestones, and public-link
   invariants.
6. **Discovery:** PostgreSQL search, typed directory, filters, bookmarks, recent activity, scenes, and
   community-class proposals.
7. **Hardening:** accessibility, CSP, performance, email, observability, backups, restore drill,
   Railway deployment, incident response, and full acceptance journey.

## Test strategy

- Pure unit tests for parsers, canonicalization, state transitions, and permission services.
- Forum contract tests that can run against Spirit or the custom fallback.
- PostgreSQL integration tests for constraints, transactions, search, and migrations.
- Permission matrix: anonymous, member, owner, contributor, blocked member, instructor, moderator,
  administrator.
- Browser journey tests for registration through searchable public knowledge.
- Critical media-validation and authorization modules target complete branch coverage. Repository-wide
  coverage begins at 85% and may not decrease.

CI must run Ruff, mypy, migration drift checks, pytest with coverage, Django deployment checks, and a
dependency audit. Production-like tests use PostgreSQL and Redis rather than SQLite.

