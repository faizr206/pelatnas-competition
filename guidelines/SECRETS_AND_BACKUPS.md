# Secrets and Backups

## Local environment files

- Use `.env` for local development secrets.
- Keep `.env.example` in the repository as the non-secret reference file.
- Never commit real credentials to source control.

## Secrets handling

- Prefer environment injection or a secret manager in non-local environments.
- Keep staging and production secrets separate.
- Rotate credentials when they are exposed or replaced.

## Backups

- Back up PostgreSQL daily.
- Back up storage metadata and the important files needed to restore datasets and critical artifacts.
- Keep backup copies somewhere separate from the primary runtime storage.

## Scope for MVP

- This document is the minimum backup and secret policy for Phase 0 and MVP.
- Expand it later if you add managed infrastructure, secrets rotation automation, or more granular restore procedures.
