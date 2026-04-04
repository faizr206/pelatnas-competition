# Pelatnas Competition Platform

Phase 1 MVP for a Kaggle-like competition platform.

## Stack

- Web: Next.js + TypeScript
- API: FastAPI
- Database: PostgreSQL
- Queue: Redis + Celery
- Storage: Garage

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

## Phase 1 scope

This repo implements the locked Phase 0 and Phase 1 decisions from [guidelines/PHASE_0_GUIDELINES.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/guidelines/PHASE_0_GUIDELINES.md) and [guidelines/PHASE_1_GUIDELINES.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/guidelines/PHASE_1_GUIDELINES.md):

- monorepo layout and local Docker runtime
- session auth with login, me, and logout
- admin competition creation and single-phase configuration
- dataset upload and version history
- CSV or notebook submission upload
- worker-backed scoring and persisted leaderboard projection
- retention cleanup task skeletons plus docs
- migration baseline and CI checks

## Quick start

1. Copy `.env.example` to `.env`.
2. Replace `GARAGE_RPC_SECRET` with a real 64-hex-character value, for example `openssl rand -hex 32`.
3. Leave `GARAGE_REPLICATION_FACTOR=1` unless you are running a multi-node Garage cluster.
4. Run `docker compose up --build`.
5. Wait for `data/garage/env` to be created by the Garage bootstrap service.
6. Open `http://localhost:3000`.
7. Sign in with the credentials from `.env`.
8. Use the dashboard to create a competition, upload a dataset version, submit a CSV or notebook file, and watch the queued job complete.

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
- Remote worker setup: [docs/operations/REMOTE_WORKER_SETUP.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/operations/REMOTE_WORKER_SETUP.md)
- Sandbox policy: [docs/security/SANDBOX_POLICY.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/security/SANDBOX_POLICY.md)
- Phase 0 notes: [docs/architecture/PHASE_0_IMPLEMENTATION.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/architecture/PHASE_0_IMPLEMENTATION.md)
- Phase 1 notes: [docs/architecture/PHASE_1_IMPLEMENTATION.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/architecture/PHASE_1_IMPLEMENTATION.md)
- Retention policy: [docs/operations/RETENTION_POLICY.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/operations/RETENTION_POLICY.md)
