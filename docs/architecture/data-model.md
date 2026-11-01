# Data model and invariants

## Identity and location

`User` uses a UUID primary key and unique email for authentication. Display names may be pseudonyms.
Each account also receives an opaque `member-<random>` internal handle; it is not a verified identity
and is not used for login.
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

Knowledge has three public forms: open discussions, living pages, and reviewed editions. A
`KnowledgePage` has a permanent identity, named contributors, dance styles, sources, and linked
discussions. Content lives in append-only `KnowledgeRevision` snapshots with edit summaries.
`ReviewedEdition` captures one revision as an immutable publication with an explicit scope and named
reviewers; it does not replace or close the living page. Projects have contributors, discussions,
video references, and milestones. Application services prevent an unlisted video from being attached
to public knowledge.

`Movement` stores a normalized knowledge node or an attributed catalog record. `MovementAlias`
records school, language, or regional names without forcing one vocabulary. `MovementRelationship`
connects prerequisites, components, variations, and related movements. Every edge records provenance
and a status of proposed, community accepted, or disputed; imported and name-inferred edges never
silently become facts.

`Curriculum` identifies an attributed teaching system independently of its concepts. A version owns
ordered `CurriculumModule` records, while `ModuleConcept` connects modules to stable `Movement`
concept nodes. The same concept may therefore appear in several modules or curricula without being
duplicated. Module membership represents `TAUGHT_IN`; proposed prerequisite edges remain separate so
source ordering is not silently presented as universal pedagogy.

`SourceReference` stores the submitted and canonical URL, exact hostname, provider classification,
attribution, and moderation status. `PostCitation` gives references a stable number within a post.
Only exact supported-provider or allowlisted domains are immediately clickable; other safe HTTPS
destinations remain visible but unclickable until staff review.

## Moderation

Blocks are directional and cannot target the same account. Reports use UUID target identifiers and
typed target names. Moderator actions are append-only audit records tied to a report.

