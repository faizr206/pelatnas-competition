# API Guidelines

This file describes both the target API direction and the current Phase 1 contract the web app already depends on.

## General rules

- Use REST first.
- Keep endpoints resource-oriented.
- Use async jobs for long-running work.
- Never run submission execution inside request handlers.
- Return stable error shapes.

## Example route groups

### Auth
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

### Competitions
- `GET /competitions`
- `POST /competitions`
- `GET /competitions/{slug}`
- `PATCH /competitions/{slug}`

### Datasets
- `POST /competitions/{slug}/datasets`
- `GET /competitions/{slug}/datasets`

### Submissions
- `POST /competitions/{slug}/submissions`
- `GET /competitions/{slug}/submissions`
- `GET /submissions/{id}`
- `GET /submissions/{id}/logs`
- `GET /submissions/{id}/artifacts`

### Jobs
- `GET /jobs/{id}`
- `POST /jobs/{id}/retry`

### Leaderboard
- `GET /competitions/{slug}/leaderboard`
- `GET /competitions/{slug}/leaderboard/public`
- `GET /competitions/{slug}/leaderboard/private`

## Response conventions

Return consistent envelopes for errors, for example:

```json
{
  "error": {
    "code": "submission_invalid",
    "message": "Submission manifest is missing the entrypoint field."
  }
}
```

Current implementation note:

- success responses are currently raw JSON objects/lists from FastAPI response models
- many error responses currently use FastAPI's `detail` field
- frontend code must handle `detail` today unless the backend is updated to normalize errors

## Job states

Recommended states:
- pending
- queued
- running
- collecting
- scoring
- completed
- failed
- cancelled
- timed_out

## Idempotency

Use idempotency keys for:
- submission creation
- file upload finalization
- retry actions

## Versioning

Add API versioning early:
- `/api/v1/...`

## Authz rules

- Keep the role model simple: one admin, everyone else is a participant.
- Participants can read only their own private artifacts.
- Admin can inspect all jobs and manage all competition settings.

## Current Phase 1 endpoint auth matrix

### Public read endpoints

- `GET /api/v1/competitions`
- `GET /api/v1/competitions/{slug}`
- `GET /api/v1/competitions/{slug}/leaderboard`
- `GET /api/v1/competitions/{slug}/leaderboard/public`
- `GET /api/v1/competitions/{slug}/leaderboard/private`

### Authenticated participant endpoints

- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`
- `GET /api/v1/competitions/{slug}/datasets`
- `GET /api/v1/datasets/{dataset_id}/download`
- `GET /api/v1/competitions/{slug}/submissions`
- `POST /api/v1/competitions/{slug}/submissions`
- `GET /api/v1/submissions/{id}`
- `GET /api/v1/submissions/{id}/logs`
- `GET /api/v1/submissions/{id}/artifacts`
- `GET /api/v1/jobs/{id}`

### Admin-only endpoints

- `POST /api/v1/competitions`
- `PATCH /api/v1/competitions/{slug}`
- `POST /api/v1/competitions/{slug}/datasets`

## Current frontend dependency notes

The web app currently assumes:

- `GET /api/v1/competitions` is enough to build the landing and competitions index pages
- `GET /api/v1/competitions/{slug}` returns all rule/limit fields needed for the `Overview` and `Rules` tabs
- `GET /api/v1/competitions/{slug}/datasets` returns full version history, with exactly one dataset usually marked `is_active`
- `GET /api/v1/competitions/{slug}/submissions` is user-scoped, not competition-global
- `POST /api/v1/competitions/{slug}/submissions` returns a job object, not the submission object
- `GET /api/v1/jobs/{id}` is the source of truth for active submission polling
- leaderboard rows are already ranked and should not be re-ranked in the frontend
