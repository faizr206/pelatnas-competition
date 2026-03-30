# Secrets and Backups

## Local environment

- Keep real local secrets in `.env`.
- Treat `.env.example` as the only committed reference file.
- Do not commit real credentials, API keys, or copied production values.

## Phase 0 secrets policy

- Session secrets come from `SESSION_SECRET`.
- Database and Redis connection strings come from environment variables.
- Non-local environments must inject secrets outside source control.
- Replace exposed credentials immediately.

## Backup policy

- Back up PostgreSQL daily.
- Back up dataset files and important submission artifacts from local storage.
- Store backups separately from the active runtime machine.
- Verify restore steps before moving beyond local-only deployment.

## Minimum restore scope

- PostgreSQL schema and data
- dataset files
- critical submission artifacts
- `.env.example` for configuration reference, never the real `.env`

