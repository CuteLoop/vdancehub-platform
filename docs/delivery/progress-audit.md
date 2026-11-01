# MVP progress audit

Audit date: 2026-11-01  
Audited revision: `479b69a`

## Executive status

VDanceHub is a tested pre-alpha knowledge and discussion prototype. The repository foundation,
authentication base, safe external-video parser, attributed Bachata movement directory, discussion
replies, and deployment configuration exist. The defining cross-product acceptance journey does not
yet work end to end.

No item in the 12-item alpha acceptance checklist is complete in full. Several have production-grade
foundations, but most still need member-facing workflows and permission enforcement. A reasonable
engineering estimate is roughly **40% of the thin-alpha implementation**, with the important caveat
that launch hardening and operational readiness are weighted late in the plan.

## Evidence at this revision

- GitHub Actions passes against PostgreSQL: tests, Ruff, formatting, strict mypy, migration drift,
  coverage, Django deployment checks, and dependency audit.
- 52 automated tests pass with 90% repository coverage.
- The local demonstration database contains 37 discussion topics, 47 movement/concept nodes,
  48 proposed relationships, and 27 attributed source references.
- The Bachata seed is explicit and idempotent; it does not download or host third-party media.
- Railway configuration exists, but this checkout is not linked to a Railway project and no Railway
  production deployment has been verified.

## Acceptance checklist audit

| Acceptance item | Status | Implemented now | Missing before completion |
| --- | --- | --- | --- |
| Registration, profiles, reporting, blocking, moderation | Partial | Allauth email identity, pseudonymous handle/display name, adult confirmation, report/block/action models | End-to-end signup/email delivery test, profile UI, report/block UI, enforcement, moderator queue and audit workflows |
| Typed questions, feedback, resources, discussions | Partial | Typed topic model, directory, detail page, safe replies, closed/removed states | Member topic creation/editing, pagination, moderation tools, feedback-thread integration |
| Search, tags, bookmarks, filters, recent activity | Partial | Movement name/alias search, tags, style/category/difficulty filters | PostgreSQL full-text search, bookmarks, activity filters, recent-activity view, pagination |
| Timestamped feedback with consent and rules | Partial | Consent-gated unlisted request creation, safe YouTube/Instagram model, timestamped-feedback model | Feedback reply UI/service, discussion creation, timestamp controls, withdrawal/reporting, discovery/privacy headers |
| Instructor profiles and offers | Model only | Profile and offer models | Create/edit/publish UI, directory, detail page, authorization, tests |
| Reviewed scheduling/payment links | Model/service only | HTTPS validation and staff-only approval method | Review queue/admin workflow, approved-link rendering, owner workflow, rejection/audit UI |
| Public projects with contributors and milestones | Model only | Project, contributor, discussion/reference, milestone models | Routes, templates, CRUD, contributor permissions, tests |
| Editable guides with immutable revisions | Model only | Knowledge page and append-only revision-shaped models | Editing/publishing workflow, permission service, immutable-update enforcement, history UI, tests |
| Safe cross-linking | Partial | Movement-to-discussion links and numbered attributed post references | Guide/project/media linking workflows and visibility invariants across every linked object |
| Approximate local scenes | Model only | City/region/country community model and user location fields | Selection, directory, privacy-aware filters, scene pages, tests |
| Remote instructor filtering | Model only | `remote_available` field | Instructor directory and filters |
| Community-class proposals and funding links | Model only | Proposal and reviewed external-link relationships | Public workflow, organizer accountability, review UI, transparency display, tests |

## Defining journey audit

1. **Register and select a community:** registration foundation exists; community selection does not.
2. **Create an unlisted feedback request:** works for an adult-confirmed authenticated user.
3. **Receive timestamped feedback:** model exists; no usable reply workflow.
4. **Discover a mentor:** models exist; no directory or profiles are exposed.
5. **Open an approved booking link:** validation/approval logic exists; no public workflow is exposed.
6. **Reuse the discussion in a guide/project:** movement discussions link correctly; guide/project
   contribution workflows do not exist.
7. **Find the result through search:** movement name/alias search works; cross-content PostgreSQL
   search does not.

The first vertical slice therefore stops after feedback-request creation. The next release target
should complete steps 2–3 before adding more catalog data.

## Highest-priority gaps and risks

1. **Feedback is not connected to discussion.** Creating a request does not create a discussion
   thread, and `TimestampedFeedback` has no member-facing route or form.
2. **Safety models are not safety controls yet.** Reports and blocks are stored in models only; they
   cannot be submitted and blocks are not enforced when listing or replying.
3. **Unlisted privacy needs hardening.** Add `noindex`/non-discovery behavior, withdrawal, participant
   reporting, and permission tests around every route that can expose a video reference.
4. **Production email is unspecified.** Allauth requires verified email, but production SMTP/provider
   settings and delivery monitoring are not configured or tested.
5. **Mentoring and external-link review have no UI.** Staff-only model methods are insufficient for
   an operational moderation queue.
6. **No submission throttling exists.** Login protection depends on Allauth defaults, while discussion,
   feedback, and reference submissions have no application rate limits.
7. **Deployment is configuration-only.** Railway files exist, but there is no linked project, verified
   public release, dependency-aware readiness check, backup, or restore drill.
8. **Production dependency reproducibility is incomplete.** CI audits resolved dependencies, but the
   Docker build installs version ranges rather than a locked production set.
9. **Browser-level acceptance and accessibility coverage are absent.** Current tests are primarily
   model/view tests; the complete mobile journey and CSP behavior still need browser verification.

## Recommended next implementation slice

Complete one secure feedback journey before building more breadth:

1. Creating a feedback request atomically creates its typed discussion and first post.
2. An adult member can submit timestamped constructive feedback through that discussion.
3. The owner can withdraw the request; anonymous discovery and indexing remain disabled.
4. A participant can report the footage or a reply, and a moderator can de-list it with an audited
   action.
5. Block relationships are enforced in the feedback and discussion views.
6. Add rate limits and permission-matrix tests, then a browser test for the whole slice.

After that slice passes, expose the mentor directory and reviewed booking link so the first five
steps of the defining journey work together.
