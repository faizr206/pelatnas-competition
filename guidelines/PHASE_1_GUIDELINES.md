# Phase 1 Guidelines

Phase 1 is the MVP competition flow. Keep it simple, single-phase, and configuration-driven so competition-specific settings can be adjusted later.

## Current implementation snapshot

The repository currently implements these participant-facing pages in `apps/web`:

- `/`
  - simple competition directory
- `/competitions`
  - competition directory
- `/competitions/[slug]`
  - competition workspace with `Overview`, `Data`, `Leaderboard`, `Rules`, and `Submissions`
- `/login`
  - session login form with redirect support

This means future UI work should start from the current route contract rather than inventing a fresh page map.

## Locked decisions

- Competition type: simple competition
- Competition phases: one phase only
- Dataset history: old dataset versions stay visible
- Submission types: CSV file or Jupyter notebook
- Scoring: competition-specific and flexible
- Scoring metric: defined by the admin per competition
- Leaderboard: use the current leaderboard model
- Roles: one admin, everyone else is a participant
- Job lifecycle: use the Phase 1 job states listed below
- Retention: use the retention rules listed below
- Constraints: use the limits listed below, but keep them configurable later

## Phase 1 job states

- `pending` - submission created, not yet queued
- `queued` - waiting for worker
- `running` - execution started
- `collecting` - gathering outputs and logs
- `scoring` - computing score
- `completed` - success
- `failed` - execution or scoring failed
- `timed_out` - exceeded time limit
- `cancelled` - manually stopped

## Retention rules

- datasets: permanent
- scores: permanent
- submission source: 30 days
- logs: 14 days
- artifacts: 14 days
- best submissions: permanent

## Phase 1 constraints

- 5 submissions per day
- 20 minute runtime
- 4 GB RAM
- 2 CPU
- no internet
- no custom Dockerfiles

## What to build in Phase 1

1. Competition CRUD for a simple single-phase competition.
2. Dataset upload and versioning with old versions still visible.
3. Submission upload for CSV and notebook files.
4. Submission validation and job creation.
5. A competition-specific scoring configuration model.
6. A leaderboard backed by persisted scores and best-submission selection logic.
7. Retention cleanup jobs for source archives, logs, and artifacts.
8. Admin controls for competition setup and scoring metric configuration.
9. Basic participant views for submissions, scores, and leaderboard.

## Current frontend requirements for Phase 1

- Keep the landing page simple and avoid leaderboard pressure on first view.
- Use the competition page as the richer Kaggle-style workspace.
- Read competition limits and allowed submission types from backend competition fields.
- Treat datasets and submissions as authenticated resources.
- Treat leaderboard as a backend projection, not a frontend computation.
- Keep top navigation size and spacing consistent across pages.
- When changing routes or API shapes, update `guidelines/CURRENT_IMPLEMENTATION_GUIDE.md`.

## Phase 1 completion criteria

- An admin can create and configure a competition.
- A participant can upload a CSV or notebook submission.
- The system queues the job, runs it, scores it, and stores the result.
- The leaderboard updates from persisted score records.
- Dataset history remains visible.
- Retention rules are documented and can be enforced later by background cleanup jobs.

## Keep for later

- Do not add teams.
- Do not add a second phase to the competition model yet.
- Do not hard-code the limits if you can store them as competition settings.
