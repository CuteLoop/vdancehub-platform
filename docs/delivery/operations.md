# Operations baseline

## Configuration

Production reads `DJANGO_SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, and `ALLOWED_HOSTS` from the hosting
secret store. Never commit real credentials or copy production data into development.

## Deployment

Railway detects the root Dockerfile. `railway.toml` runs migrations as an isolated pre-deploy command,
and the Docker startup command applies any still-pending migrations before starting Gunicorn as a
portable safety net. The configured `/health/` deployment check must
return `2xx` before Railway activates a release; it must later gain dependency-aware readiness without
leaking configuration.

## Backups and recovery

Take daily encrypted PostgreSQL backups with 35-day expiry. Monthly, restore the newest backup into an
isolated environment and verify account counts, visibility/permission samples, revisions, reports,
and search regeneration. Record recovery point and recovery time.

## Incidents

Security reports go through `SECURITY.md`, not public issues. For footage-consent or rights complaints,
remove discovery/embedding first, preserve restricted evidence, acknowledge the reporter, investigate,
record the decision, and notify affected account owners without exposing reporter details.

