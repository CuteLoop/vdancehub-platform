# Security, privacy, and safety baseline

## Trust boundaries

Treat member text, URLs, provider content, forum package output, outbound booking pages, CI artifacts,
and administrator-entered moderation notes as untrusted. External providers control their own access,
tracking, retention, and availability.

## Priority threats and controls

| Threat | Required control |
| --- | --- |
| Hostname confusion, SSRF, redirect abuse | Exact HTTPS provider parsing; no server-side fetches or redirects |
| XSS and embed injection | Template autoescape, restricted text formatting, generated iframe URLs, CSP |
| Unlisted disclosure | UUID routes, no indexing/search/sitemaps, owner checks, explicit public promotion |
| Footage without consent | Required attestations, reporting path, immediate de-listing on participant complaint |
| Harassment through feedback | Constructive rules, report/block, rate limits, moderation audit trail |
| Phishing through mentor/funding links | Staff review, HTTPS validation, visible destination, external/unverified warning |
| ID enumeration or broken access control | UUID identifiers plus object-level permission tests on every route |
| Account attacks | Verified email, password validation, login/submission throttling, secure sessions |
| Supply-chain compromise | Locked dependencies, dependency audit, update automation, minimal packages |

Unlisted means anyone possessing the URL can attempt access; it is not private storage. Users needing
confidential review must use an instructor-controlled workflow outside VDanceHub.

## Content and consent response

The public beta is adults-only. Submitters attest that all identifiable participants are adults and
authorized the sharing. A participant or rights-holder report immediately disables discovery and
embedding while review occurs. Moderators may restore, keep unavailable, or remove the reference and
must record a rationale.

Copyright and privacy notices need a named contact and legally reviewed process before public launch.
The platform must not claim ownership of referenced videos or imply that provider availability proves
permission.

## Retention defaults

- Withdrawn content becomes unavailable immediately and is hard-deleted after 30 days.
- Restricted moderation evidence is retained for 12 months unless law or an active investigation
  requires a documented exception.
- Production backups expire after 35 days.
- These are product defaults, not legal conclusions; complete jurisdictional review before launch.

## Release gate

Run Django deployment checks, permission-matrix tests, malicious URL regression tests, dependency audit,
backup restoration, incident tabletop, accessibility review, and a manual CSP/browser inspection. A
passing automated suite alone does not authorize public launch.

