# Competition Platform Project Docs

This folder contains a practical documentation starter pack for your Kaggle-like competition platform.

## Included files

- `PHASE_0_GUIDELINES.md` — exact Phase 0 setup checklist and locked-in decisions
- `PROJECT_STRUCTURE_GUIDE.md` — recommended repo and service structure
- `ARCHITECTURE.md` — high-level system architecture
- `ROADMAP.md` — suggested build order from MVP to scale
- `DATABASE_SCHEMA_GUIDE.md` — core entities and schema direction
- `API_GUIDELINES.md` — API conventions and endpoint design
- `EXECUTION_SANDBOX.md` — running untrusted code safely
- `SCORING_AND_LEADERBOARD.md` — evaluation and leaderboard rules
- `DEVOPS_AND_DEPLOYMENT.md` — environments, CI/CD, observability
- `SECURITY_CHECKLIST.md` — security controls to implement
- `SECRETS_AND_BACKUPS.md` — local env, backup, and secret handling rules
- `PRODUCT_REQUIREMENTS_TEMPLATE.md` — template for competition/product rules
- `CONTRIBUTING.md` — team conventions for code and PRs

## Suggested first stack

- Frontend: Next.js + TypeScript
- Backend API: FastAPI
- Database: PostgreSQL
- Queue: Redis + Celery
- Storage: local disk for v1, S3-compatible storage later
- Execution: Docker-based worker nodes
- Later scaling: Kubernetes Jobs and GPU worker pools

## Recommended reading order

1. `PROJECT_STRUCTURE_GUIDE.md`
2. `ARCHITECTURE.md`
3. `EXECUTION_SANDBOX.md`
4. `DATABASE_SCHEMA_GUIDE.md`
5. `API_GUIDELINES.md`
6. `PHASE_0_GUIDELINES.md`
7. `ROADMAP.md`
