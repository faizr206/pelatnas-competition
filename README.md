# Pelatnas Competition Platform

Phase 0 foundation for a Kaggle-like competition platform.

## Stack

- Web: Next.js + TypeScript
- API: FastAPI
- Database: PostgreSQL
- Queue: Redis + Celery
- Storage: local disk

## Repository layout

```text
apps/
  web/
  api/
  worker/
packages/
docs/
infra/
tests/
guidelines/
```

## Phase 0 scope

This repo implements the locked Phase 0 decisions from [guidelines/PHASE_0_GUIDELINES.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/guidelines/PHASE_0_GUIDELINES.md):

- monorepo layout and local Docker runtime
- session auth with login, me, and logout
- PostgreSQL, Redis, Celery worker, and local disk storage
- base competition, submission, job, score, and leaderboard records
- migration baseline and CI checks
- secrets, backups, and sandbox policy docs

## Quick start

1. Copy `.env.example` to `.env`.
2. Run `docker compose up --build`.
3. Open `http://localhost:3000`.
4. Sign in with the credentials from `.env`.
5. Use the dashboard to create a smoke-test submission and watch the queued job complete.

## Local commands

### Python

- Install: `python3 -m pip install -r requirements/dev.txt`
- Run migrations: `PYTHONPATH=. alembic -c apps/api/alembic.ini upgrade head`
- Run API: `PYTHONPATH=. uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000`
- Run worker: `PYTHONPATH=. celery -A apps.worker.worker.queue:celery_app worker --loglevel=info --concurrency=2`

### Web

- Install: `cd apps/web && npm install`
- Run: `npm run dev`

## Docs

- Secrets and backups: [docs/operations/SECRETS_AND_BACKUPS.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/operations/SECRETS_AND_BACKUPS.md)
- Sandbox policy: [docs/security/SANDBOX_POLICY.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/security/SANDBOX_POLICY.md)
- Phase 0 notes: [docs/architecture/PHASE_0_IMPLEMENTATION.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/architecture/PHASE_0_IMPLEMENTATION.md)

