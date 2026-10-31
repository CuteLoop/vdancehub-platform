# ADR 0002: Minimal native discussion backend

Status: accepted after Spirit rejection — 2026-10-31

Spirit 0.14.3 passed Django checks and fresh migrations after VDanceHub retained an opaque username
field. It nevertheless fails the production dependency gate: it hard-pins Mistune 0.8.4, for which the
2026-10-31 dependency audit reports multiple known vulnerabilities and no compatible fixed release.

VDanceHub will therefore implement only typed topics and replies in its own `discussions` app while
retaining stable thread/post facades. Reconsidering a third-party engine requires a maintained dependency
graph, clean security audit, custom-user compatibility, and no patching of package internals.

