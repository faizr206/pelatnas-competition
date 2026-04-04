# Pelatnas Competition Platform

Pelatnas Competition Platform is a self-hosted competition system for running data and notebook-based evaluations with an admin-managed workflow, persistent scoring, and worker-based execution.

It includes:

- competition management for admins
- dataset upload and version tracking
- CSV and notebook submissions
- asynchronous worker processing with Celery
- persisted scores and leaderboard projection
- worker fleet visibility in the admin panel
- S3-compatible artifact storage with Garage

## Architecture

- Web: Next.js + TypeScript
- API: FastAPI
- Worker: Celery
- Database: PostgreSQL
- Queue: Redis
- Object storage: Garage

## Repository Layout

```text
apps/
  web/        # Next.js frontend
  api/        # FastAPI application
  worker/     # Celery worker
packages/     # shared domain and infrastructure packages
docs/         # operations and security documentation
infra/        # Dockerfiles and runtime assets
tests/        # test suite
```

## What The Platform Does

### Admin workflows

- create and manage competitions
- configure a single competition phase
- upload datasets and track versions
- configure scoring inputs and constraints
- monitor workers and submission tasks from the admin panel

### Participant workflows

- browse competitions
- submit CSV files or notebooks
- monitor submission and job status
- view scores and leaderboard results

### Worker workflows

- pull queued jobs from Redis
- download inputs from Garage
- run scoring and artifact generation
- persist job, score, and leaderboard updates
- report heartbeat and GPU availability to the admin panel

## Prerequisites

For a standard local deployment:

- Docker with Compose support

For local development without Docker:

- Python 3.12
- Node.js and npm
- PostgreSQL
- Redis

## Quick Start

### 1. Create the environment file

Copy the example file:

```bash
cp .env.example .env
```

Update at least these values before you start the stack:

- `SESSION_SECRET`
- `GARAGE_RPC_SECRET`
- `GARAGE_ADMIN_TOKEN`

Generate a Garage RPC secret with:

```bash
openssl rand -hex 32
```

### 2. Set the correct bind IP

The Compose file exposes PostgreSQL, Redis, Garage, and the API on `TAILSCALE_BIND_IP`.

- If you are not using Tailscale locally, set `TAILSCALE_BIND_IP=127.0.0.1`
- If you are using Tailscale, set it to your host's `tailscale0` IPv4 address

The web app is exposed on `127.0.0.1:3000`.

### 3. Start the stack

```bash
docker compose up --build
```

The stack starts:

- `postgres`
- `redis`
- `garage`
- `garage-bootstrap`
- `api`
- `worker`
- `web`

The API container runs database migrations automatically on startup.

### 4. Wait for Garage bootstrap

`garage-bootstrap` creates `data/garage/env` with the generated storage credentials used by the API and worker containers.

### 5. Open the application

Open:

```text
http://localhost:3000
```

Default admin credentials come from `.env`:

- `DEFAULT_ADMIN_EMAIL`
- `DEFAULT_ADMIN_PASSWORD`

From there you can:

1. sign in as admin
2. create or edit a competition
3. upload a dataset
4. submit a CSV or notebook
5. monitor job execution and worker status

## GPU Worker Support

GPU support is optional.

- On CPU-only hosts, run the normal stack and the worker will report `GPU available: no`
- On NVIDIA hosts with NVIDIA Container Toolkit installed, start the worker with the GPU override

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build worker
```

When the worker heartbeats successfully, the admin worker panel will show `GPU available: yes`.

GPU runtime setup instructions are documented in [docs/operations/NVIDIA_CONTAINER_TOOLKIT.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/operations/NVIDIA_CONTAINER_TOOLKIT.md).

## Local Development

### Python services

Install dependencies:

```bash
python3 -m pip install -r requirements/dev.txt
```

Run migrations:

```bash
PYTHONPATH=. alembic -c apps/api/alembic.ini upgrade head
```

Run the API:

```bash
PYTHONPATH=. uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000
```

Run the worker:

```bash
PYTHONPATH=. celery -A apps.worker.worker.queue:celery_app worker --loglevel=info --concurrency=2
```

### Web

Install frontend dependencies:

```bash
cd apps/web && npm install
```

Run the frontend:

```bash
npm run dev
```

## Operations And Reference Docs

- Remote worker deployment: [docs/operations/REMOTE_WORKER_SETUP.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/operations/REMOTE_WORKER_SETUP.md)
- NVIDIA Container Toolkit setup: [docs/operations/NVIDIA_CONTAINER_TOOLKIT.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/operations/NVIDIA_CONTAINER_TOOLKIT.md)
- Secrets and backup guidance: [docs/operations/SECRETS_AND_BACKUPS.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/operations/SECRETS_AND_BACKUPS.md)
- Retention policy: [docs/operations/RETENTION_POLICY.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/operations/RETENTION_POLICY.md)
- Sandbox and worker execution policy: [docs/security/SANDBOX_POLICY.md](/Users/faiz.ramadhan/Documents/Programming/pelatnas-competition/docs/security/SANDBOX_POLICY.md)

## Testing

Run the backend test suite with:

```bash
pytest
```
