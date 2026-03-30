# Competition Platform Project Docs

This folder contains a practical documentation starter pack for your Kaggle-like competition platform.

## Included files

- `CURRENT_IMPLEMENTATION_GUIDE.md` — current route map, auth matrix, and frontend/backend contract
- `PHASE_0_GUIDELINES.md` — exact Phase 0 setup checklist and locked-in decisions
- `PHASE_1_GUIDELINES.md` — exact Phase 1 setup checklist and competition rules
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

If you need to understand how the repo behaves today, start with `CURRENT_IMPLEMENTATION_GUIDE.md` before reading the broader architecture docs.

1. `CURRENT_IMPLEMENTATION_GUIDE.md`
2. `PROJECT_STRUCTURE_GUIDE.md`
3. `ARCHITECTURE.md`
4. `EXECUTION_SANDBOX.md`
5. `DATABASE_SCHEMA_GUIDE.md`
6. `API_GUIDELINES.md`
7. `PHASE_0_GUIDELINES.md`
8. `PHASE_1_GUIDELINES.md`
9. `ROADMAP.md`
