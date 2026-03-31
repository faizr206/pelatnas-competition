# Current Implementation Guide

Use this document as the first-stop reference for the repository's current Phase 1 behavior. It is intentionally concrete. Read this before exploring the codebase when you need to understand the current frontend/backend contract.

## Current stack

- Web: Next.js App Router, TypeScript, Tailwind
- API: FastAPI
- Worker: Celery-style async job execution
- Database: PostgreSQL
- Queue: Redis

## Current user-facing routes

### Web routes

- `/`
  - simple competition directory
  - same content model as `/competitions`
- `/competitions`
  - competition directory page
  - backed by `GET /api/v1/competitions`
- `/competitions/[slug]`
  - Kaggle-style competition workspace
  - currently implemented tabs:
    - `Overview`
    - `Data`
    - `Leaderboard`
    - `Rules`
    - `Submissions`
- `/login`
  - email/password login form
  - supports `?next=/some/path` redirect after successful login
- `/profile`
  - signed-in account summary page
  - exposes current session identity and quick links
- `/admin`
  - admin-only competition management page
  - main admin hub for creation and edit routing
- `/admin/new`
  - dedicated create-competition screen
- `/admin/competitions/[slug]`
  - dedicated edit screen for one competition
  - supports phase edits and scoring setup

### Current route ownership in `apps/web`

- `src/app/page.tsx`
  - homepage competition directory
- `src/app/competitions/page.tsx`
  - explicit competitions index
- `src/app/competitions/[slug]/page.tsx`
  - competition workspace entry point
- `src/app/login/page.tsx`
  - login entry point
- `src/app/profile/page.tsx`
  - profile entry point
- `src/app/admin/page.tsx`
  - admin entry point
- `src/app/admin/new/page.tsx`
  - create competition entry point
- `src/app/admin/competitions/[slug]/page.tsx`
  - edit competition entry point
- `src/components/competitions-directory.tsx`
  - live competition list UI
- `src/components/competition-workspace.tsx`
  - competition detail workspace UI
- `src/components/login-form-page.tsx`
  - login form behavior
- `src/components/profile-page.tsx`
  - signed-in profile summary UI
- `src/components/admin-panel-page.tsx`
  - admin hub UI
- `src/components/admin-create-competition-page.tsx`
  - competition creation UI
- `src/components/admin-edit-competition-page.tsx`
  - single-competition edit UI
- `src/components/admin-competition-form.tsx`
  - shared competition form primitives
- `src/components/site-header.tsx`
  - shared top navigation shell
- `src/components/session-actions.tsx`
  - signed-in header actions including logout
- `src/lib/api.ts`
  - all current frontend API calls
- `src/lib/competition-types.ts`
  - all current frontend API types

## Current UX rules

### Landing and competitions index

- Keep the index lightweight.
- Show only competition discovery information:
  - title
  - description
  - status
  - scoring metric
  - submission limit
  - phase dates
- Do not show rankings on the landing page.

### Competition workspace

- Keep the current light gray header and white content style.
- The top navigation must remain dimensionally consistent across pages.
- Current desktop header rule:
  - shared header height should stay at `75px`
  - nav pills should stay at `h-9`
  - right-side action control should visually align with the nav pills
- The competition workspace should feel richer than the landing page, but still use the same visual language.

### Current tab behavior

- `Overview`
  - show competition description, evaluation summary, timeline, and sidebar facts
- `Data`
  - show dataset versions and download links
  - requires authenticated session because the backend requires auth for dataset endpoints
- `Leaderboard`
  - show ranking table
  - supports public/private projection toggle
  - both projections are currently exposed by the backend as read endpoints
- `Rules`
  - must mirror competition limits and platform constraints from backend fields and Phase 1 docs
- `Submissions`
  - authenticated user view only
  - upload flow:
    1. choose submission type
    2. choose file
    3. submit
  - show current job lifecycle and submission history

## Current backend contract the frontend relies on

### Base URL

- Frontend env var: `NEXT_PUBLIC_API_URL`
- Default value:
  - `http://localhost:8000/api/v1`

### Current auth behavior

- Session-based auth
- Login endpoint:
  - `POST /api/v1/auth/login`
- Session probe:
  - `GET /api/v1/auth/me`
- Logout endpoint:
  - `POST /api/v1/auth/logout`

### Current authenticated navigation behavior

- Signed-in users now get header actions for:
  - `Profile`
  - `Logout`
- Admin users additionally get:
  - `Admin`
- Competition workspace now shows an `Edit Competition` shortcut for admins.
- The dedicated competition edit screen now includes:
  - `solution.csv` upload
  - editable Python metric code
  - built-in metric templates such as `mse_metric.py`

### Auth requirement matrix

- public:
  - `GET /api/v1/competitions`
  - `GET /api/v1/competitions/{slug}`
  - `GET /api/v1/competitions/{slug}/leaderboard`
  - `GET /api/v1/competitions/{slug}/leaderboard/public`
  - `GET /api/v1/competitions/{slug}/leaderboard/private`
- authenticated user required:
  - `GET /api/v1/auth/me`
  - `GET /api/v1/competitions/{slug}/datasets`
  - `GET /api/v1/datasets/{dataset_id}/download`
  - `GET /api/v1/competitions/{slug}/submissions`
  - `POST /api/v1/competitions/{slug}/submissions`
  - `GET /api/v1/jobs/{job_id}`
  - `GET /api/v1/submissions/{submission_id}`
  - `GET /api/v1/submissions/{submission_id}/logs`
  - `GET /api/v1/submissions/{submission_id}/artifacts`
- admin required:
  - `POST /api/v1/competitions`
  - `PATCH /api/v1/competitions/{slug}`
  - `POST /api/v1/competitions/{slug}/datasets`
  - `GET /api/v1/competitions/{slug}/scoring-config`
  - `PUT /api/v1/competitions/{slug}/scoring-config`

### Current response-shape reality

- Successful responses currently return raw JSON objects/lists matching the Pydantic response schemas.
- Error responses currently mostly use FastAPI's `detail` field.
- Do not assume the aspirational `{ error: { code, message } }` envelope is implemented everywhere yet.

## Current competition model fields that matter to the web app

The web app currently depends on these competition fields:

- `slug`
- `title`
- `description`
- `visibility`
- `status`
- `scoring_metric`
- `scoring_direction`
- `best_submission_rule`
- `max_submissions_per_day`
- `max_runtime_minutes`
- `max_memory_mb`
- `max_cpu`
- `allow_csv_submissions`
- `allow_notebook_submissions`
- `source_retention_days`
- `log_retention_days`
- `artifact_retention_days`
- `phases[]`

The web app currently depends on these phase fields:

- `name`
- `starts_at`
- `ends_at`
- `submission_limit_per_day`
- `scoring_version`
- `rules_version`

## Current competition workspace data-loading rules

- Load competition details and public leaderboard immediately.
- Probe session with `GET /auth/me`.
- If signed in:
  - load datasets
  - load submissions
- Load private leaderboard lazily when the user switches to the private projection.
- When a submission is created:
  - refresh submissions
  - refresh leaderboard
  - poll the job endpoint while status is one of:
    - `pending`
    - `queued`
    - `running`
    - `collecting`
    - `scoring`

## Current Phase 1 defaults in backend bootstrap

- default admin email:
  - `admin@example.com`
- default admin password:
  - `admin1234`
- default competition slug:
  - `phase-0-smoke-test`
- default competition title:
  - `Phase 0 Smoke Test`

Treat these as local bootstrap defaults, not product copy.

## When changing backend schemas or routes

Always update these frontend files together:

- `apps/web/src/lib/competition-types.ts`
- `apps/web/src/lib/api.ts`
- `apps/web/src/components/competition-workspace.tsx`
- `apps/web/src/components/competitions-directory.tsx`
- `apps/web/src/components/login-form-page.tsx`

Also update this document and the files below if the contract changes:

- `guidelines/API_GUIDELINES.md`
- `guidelines/UI_GUIDELINES.md`
- `guidelines/PHASE_1_GUIDELINES.md`

## Current design intent summary

- Homepage and `/competitions` should stay simple and low-pressure.
- `/competitions/[slug]` should be the richer Kaggle-style workspace.
- Keep the current minimalist visual style:
  - gray top bar
  - white content surfaces
  - thin borders
  - compact typography
  - black primary actions
- Prefer a small number of consistent layout primitives over ad hoc one-off styling.
