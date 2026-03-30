# Roadmap

## Phase 0: foundation
- choose stack
- initialize monorepo
- setup auth
- setup postgres, redis, local storage
- create base CI
- see `PHASE_0_GUIDELINES.md` for the exact setup checklist and locked-in decisions

## Phase 1: MVP
- simple competition CRUD
- single-phase competition setup
- dataset upload and versioning
- CSV or notebook submission
- async job queue
- score persistence
- simple leaderboard
- admin panel for competition creation
- see `PHASE_1_GUIDELINES.md` for the exact competition rules and MVP constraints

## Phase 2: code submission
- submission archive upload
- standard runtime contract
- Docker executor
- logs and artifacts
- timeout, CPU, memory limits
- run history page

## Phase 3: model-aware scoring
- submission manifest
- architecture extraction where possible
- score formula with metric plus complexity penalties
- reproducibility checks

## Phase 4: scale and hardening
- rate limits
- quotas
- private/public leaderboard split
- retries and dead-letter handling
- observability dashboards
- audit trail expansion

## Phase 5: advanced platform
- team submissions
- GPU job pools
- notebook or devbox support
- challenge templates
- organization accounts
