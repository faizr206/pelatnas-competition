# Phase 0 Guidelines

Phase 0 is the foundation pass. The goal is to get the repo, local runtime, auth skeleton, queue/worker flow, and core policy decisions in place before MVP work starts.

## Locked decisions

- Frontend stack: Next.js + TypeScript
- Backend stack: FastAPI
- Database: PostgreSQL
- Queue: Redis + Celery
- Storage: local disk for now
- Worker model: any worker can be started independently, connect to the queue, and pull jobs when it has capacity
- Auth: session auth
- Architecture: modular monolith for product logic, separate worker tier for execution
- Deployment target: local Docker only for now
- Competition phases: phase 1 is file submission, phase 2 is code submission
- Competition structure: create competitions with phases from the start
- Teams: disabled for now
- Leaderboard: public and private views
- Leaderboard freeze: freeze after competition end
- Leaderboard ranking: tie-break by submission time
- Best submission selection: adjustable by competition admin
- Sandbox policy: code runs as non-root, without outbound internet, with 2 CPU, 4 GB RAM, 20 minute timeout, and only approved base images; user-provided Dockerfiles are not allowed
- CI: enforce the required PR checks listed in this guide
- Backups and secrets: use local `.env`, repo `.env.example`, daily DB backups, and storage backups for datasets and important artifacts

## What to do in Phase 0

1. Create the monorepo and lock the top-level layout.
2. Scaffold `apps/web`, `apps/api`, and `apps/worker`.
3. Add the shared packages you know you need now: `core`, `db`, `auth`, `competitions`, `submissions`, `scoring`, `leaderboard`, `storage`, `execution`, and `observability`.
4. Implement session auth endpoints and guards.
5. Stand up PostgreSQL, Redis, and local disk storage in Docker Compose.
6. Build the worker as a queue consumer that can be started on any machine.
7. Add the base job states, job records, and submission records needed for Phase 1.
8. Wire the CI checks required on every PR.
9. Add migration validation and a working local database migration baseline.
10. Create `SECRETS_AND_BACKUPS.md` and document `.env`, `.env.example`, DB backup, and storage backup rules.
11. Add the sandbox policy to the worker docs so Phase 2 does not drift from the agreed limits.

## Phase 0 completion criteria

- `docker compose up` brings up web, api, worker, postgres, and redis successfully.
- A worker process can connect to the queue and pull a job when capacity is available.
- Session auth works end to end for the basic login/me/logout flow.
- Database migrations run cleanly from a fresh local environment.
- CI passes for the required backend, frontend, worker, and migration checks.
- The backup and secrets document exists and reflects the agreed rules.

## Do not do yet

- Do not add teams.
- Do not add code execution features beyond the sandbox policy and worker skeleton.
- Do not add Kubernetes-only deployment paths.
- Do not introduce S3, MinIO, or other remote storage as the default v1 storage path.
- Do not implement model-aware scoring or advanced leaderboard logic yet.
