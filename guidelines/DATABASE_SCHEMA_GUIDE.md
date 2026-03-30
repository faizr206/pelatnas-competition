# Database Schema Guide

## Core tables

### `users`
- id
- email
- display_name
- status
- created_at
- updated_at

### `teams`
- id
- name
- owner_user_id
- created_at

### `team_members`
- team_id
- user_id
- role
- joined_at

### `competitions`
- id
- slug
- title
- description
- visibility
- status
- created_by
- created_at
- updated_at

### `competition_phases`
- id
- competition_id
- name
- starts_at
- ends_at
- submission_limit_per_day
- scoring_version
- rules_version

Notes:
- Phase 1 uses a single phase per competition.

### `datasets`
- id
- competition_id
- name
- version
- storage_path
- checksum
- is_active
- created_at

Notes:
- keep old dataset versions visible
- `is_active` marks the current dataset version, not a hidden archive

### `submissions`
- id
- competition_id
- phase_id
- user_id
- team_id
- submission_type
- source_archive_path
- manifest_path
- runtime_image
- runtime_image_digest
- status
- created_at

Notes:
- `submission_type` should cover `csv` and `notebook` for Phase 1

### `jobs`
- id
- submission_id
- job_type
- status
- queued_at
- started_at
- finished_at
- worker_id
- retry_count
- failure_reason

### `submission_artifacts`
- id
- submission_id
- artifact_type
- storage_path
- checksum
- size_bytes
- created_at

### `scores`
- id
- submission_id
- metric_name
- metric_value
- score_value
- scoring_version
- created_at

Notes:
- keep score records permanent
- scoring logic is competition-specific and versioned

### `leaderboard_entries`
- id
- competition_id
- phase_id
- user_id
- team_id
- best_submission_id
- score_value
- rank
- visibility_type
- updated_at

Notes:
- this is the current leaderboard projection
- best submissions stay permanent

### `audit_logs`
- id
- actor_user_id
- entity_type
- entity_id
- action
- metadata_json
- created_at

## Notes

- Prefer append-only score records.
- Avoid storing only the latest score.
- Keep leaderboard projection separate from raw scores.
- Add indexes early for `competition_id`, `phase_id`, `user_id`, and `status`.
