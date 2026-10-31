# Architecture

## Context and boundaries

VDanceHub is a modular Django monolith. PostgreSQL is the source of truth. Redis is limited to shared
caching and rate limiting; background jobs are added only after a real asynchronous workload exists.
Railway is the first deployment target, while Docker and environment-based configuration preserve
portability.

The domain is divided into accounts, taxonomy, communities, discussions, media references, feedback,
mentoring, knowledge, projects, moderation, and search. Cross-domain behavior belongs in explicit
service functions; templates must not make authorization decisions.

## Discussion isolation

Domain models refer to local `DiscussionThreadRef` and `DiscussionPostRef` records. The alpha uses a
minimal native typed-topic/reply implementation. The stable facade remains so a future maintained
engine can be evaluated without changing feedback, knowledge, or project foreign keys.

Spirit was rejected because its hard-pinned Markdown dependency failed the security audit. django-machina
was not tested further because its published Django compatibility evidence is stale. See ADR 0002.

## Media-reference boundary

`VideoReference` represents an owner-scoped canonical reference. The same reference may be linked to
feedback, a project, or a guide. The database prevents duplicates for the same owner/provider/video,
but never merges another owner’s unlisted record or reveals that it exists.

Parsing is local and deterministic. The application does not request submitted URLs, follow redirects,
accept embed code, or persist provider HTML. All canonical and embed URLs are generated from validated
provider identifiers.

Public content may link only public video references. Promoting an unlisted reference requires an
explicit owner action. Withdrawal removes viewing immediately; downstream content shows an unavailable
reference rather than copying the URL.

## Search and discovery

PostgreSQL full-text search will produce a typed union of public discussions, guides, projects,
instructors, and scenes. Filters include content activity, dance style, skill level, technique tags,
country/region/city, language, and remote availability. Eligibility is enforced in query services;
unlisted records are not indexed.

## Deployment topology

One web process connects to PostgreSQL and Redis. Static assets use WhiteNoise initially. Production
requires HTTPS, secure cookies, HSTS, restrictive CSP, structured logs, error monitoring, daily database
backups, and a documented restore drill. No filesystem-persisted user media is required.

