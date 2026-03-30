# Phase 0 Implementation Notes

This repository locks the Phase 0 monorepo layout and provides the minimum end-to-end flow needed before MVP work starts.

## Implemented foundation

- `apps/web`: Next.js login and smoke-test dashboard
- `apps/api`: FastAPI API with session auth, competition listing, submission creation, and job status endpoints
- `apps/worker`: Celery worker with submission job skeleton and sandbox policy wiring
- `packages/*`: shared policy, persistence, auth, storage, scoring, and leaderboard modules
- `docker-compose.yml`: web, api, worker, postgres, and redis
- `apps/api/alembic`: working migration baseline
- `.github/workflows/ci.yml`: formatting, lint, type checks, tests, migration validation, and container builds

## Seeded bootstrap data

- one default admin user
- one default competition with one active phase

## Out of scope

- team support
- real file uploads
- real sandbox execution
- advanced leaderboard policy

