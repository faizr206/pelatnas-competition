# API Guidelines

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

## Job states

Recommended states:
- pending
- queued
- running
- collecting_artifacts
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

- Participants can read only their own private artifacts.
- Admins can inspect all jobs.
- Competition owners can modify only their competitions.
