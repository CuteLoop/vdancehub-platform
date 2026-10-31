# ADR 0003: External video references

Status: accepted — 2026-10-31

Do not host user video or accept arbitrary embed code. Parse approved YouTube and Instagram URLs
locally, store owner-scoped canonical references, and generate safe output URLs. YouTube may use the
privacy-enhanced player; Instagram begins as an external link. Unlisted is the default.

