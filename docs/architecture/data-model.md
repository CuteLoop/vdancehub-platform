# Data model and invariants

## Identity and location

`User` uses a UUID primary key and unique email for authentication. Display names may be pseudonyms.
Spirit requires a unique username field, so each account receives an opaque `member-<random>` forum
handle; it is not a verified identity and is not used for login.
Only country code, region, and city are accepted for member location. A separate `Community` represents
a public local scene.

## Discussion facade

`DiscussionThreadRef(backend, backend_id)` and `DiscussionPostRef(thread, backend_id)` are unique
adapter handles. Domain objects reference the facade, never backend internals.

## Video and feedback

`VideoReference` stores owner, provider, provider identifier, canonical URL, optional timestamp,
attribution, description, visibility, promotion time, withdrawal time, and original submitted URL for
audit. Its default visibility is unlisted.

`FeedbackRequest` requires the author to own the reference and affirm adult participation, footage
permission, and constructive-feedback rules. `TimestampedFeedback` links an optional forum post to a
nonnegative second offset; the offset is syntax-validated but not compared with remote duration.

## Mentoring and outbound links

Instructor profiles have professional names, biographies, languages, specialties, location/remote
availability, and offers. External links move through pending, approved, or rejected states and retain
reviewer/time audit data. UI may expose only approved links and must always call them external and
unverified.

## Knowledge and projects

Knowledge pages have owners and named contributors. Content lives in immutable revisions with edit
summaries. Projects have contributors, discussions, video references, and milestones. Application
services prevent an unlisted video from being attached to public knowledge.

## Moderation

Blocks are directional and cannot target the same account. Reports use UUID target identifiers and
typed target names. Moderator actions are append-only audit records tied to a report.

