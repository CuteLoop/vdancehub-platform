# ADR 0001: Django modular monolith

Status: accepted — 2026-10-31

Use Django 5.2, PostgreSQL, server-rendered templates, and domain-focused applications in one deployable
service. This minimizes operational overhead while preserving explicit boundaries. Redis supports
shared caching and throttling only; Celery and DRF require a demonstrated consumer.

