# Project Structure Guide

This guide describes how to structure the repository for a Kaggle-like competition platform that supports both file submission and code execution.

## Core principles

- Start as a modular monolith, not many microservices.
- Keep execution workers separate from the web app.
- Separate competition logic, execution runtime, and scoring policy.
- Keep all competition assets versioned.
- Design now for reproducibility, auditability, and future scaling.

## Recommended top-level structure

```text
competition-platform/
  apps/
    web/
    api/
    worker/
  packages/
    core/
    db/
    auth/
    competitions/
    submissions/
    scoring/
    leaderboard/
    storage/
    execution/
    observability/
    sdk/
  infra/
    docker/
    k8s/
    terraform/
    scripts/
  docs/
  tests/
  .github/
```

## What each folder should contain

### `apps/web`
The user-facing frontend.

Suggested stack:
- Next.js
- TypeScript
- Tailwind

Recommended internal structure:

```text
apps/web/
  src/
    app/
    components/
    features/
      competitions/
      submissions/
      leaderboard/
      admin/
    lib/
      api/
      auth/
      utils/
    hooks/
    styles/
  public/
  tests/
```

Responsibilities:
- competition listing pages
- competition detail page
- dataset and rule presentation
- submission upload flow
- job status view
- leaderboard pages
- admin UI for creating competitions

### `apps/api`
The main application backend.

Suggested stack:
- FastAPI
- SQLAlchemy or SQLModel
- Alembic
- Pydantic

Recommended internal structure:

```text
apps/api/
  app/
    main.py
    config.py
    dependencies/
    middleware/
    routers/
      auth.py
      competitions.py
      datasets.py
      submissions.py
      jobs.py
      leaderboard.py
      admin.py
    services/
    schemas/
    repositories/
    models/
    tasks/
  alembic/
  tests/
```

Responsibilities:
- authentication and authorization
- CRUD for competitions and datasets
- submission registration
- job orchestration entrypoints
- score retrieval
- leaderboard read APIs
- admin workflows

### `apps/worker`
The execution and background processing runtime.

Recommended internal structure:

```text
apps/worker/
  worker/
    main.py
    queue.py
    job_handlers/
      prepare_submission.py
      run_submission.py
      collect_artifacts.py
      score_submission.py
      update_leaderboard.py
    executors/
      docker_executor.py
      k8s_job_executor.py
    policies/
      resource_limits.py
      network_policy.py
    utils/
  tests/
```

Responsibilities:
- fetch submission package
- prepare isolated execution environment
- run code under limits
- collect logs and artifacts
- invoke scoring
- update job states
- connect to the queue and pull jobs only when capacity is available

## Packages layout

### `packages/core`
Shared constants, enums, types, common helpers.

Examples:
- job state enum
- submission status enum
- standard error codes
- environment naming rules

### `packages/db`
Database session setup and shared models.

Examples:
- base ORM models
- common timestamps
- database migration helpers

### `packages/auth`
Auth and permission helpers.

Examples:
- role definitions
- team permissions
- admin guards
- token/session utilities

### `packages/competitions`
Competition domain logic.

Examples:
- competition lifecycle
- phase handling
- dataset version rules
- submission eligibility
- rule versioning

### `packages/submissions`
Submission intake and validation.

Examples:
- upload validation
- file checksum logic
- repo archive handling
- submission manifest parsing

### `packages/scoring`
Scoring engine abstractions.

Examples:
- scoring interfaces
- custom metric runners
- architecture-aware scoring helpers
- score normalization
- tie-break logic

### `packages/leaderboard`
Leaderboard generation and ranking logic.

Examples:
- public/private leaderboard split
- ranking rules
- best submission selection
- cached leaderboard projection

### `packages/storage`
Object storage abstraction.

Examples:
- upload/download helpers
- signed URL generation
- artifact path conventions
- retention rules

### `packages/execution`
Execution contracts and sandbox interfaces.

Examples:
- runner interfaces
- mount layout rules
- resource limit schema
- trusted image policy
- runtime manifest format

### `packages/observability`
Logging, tracing, metrics, audit helpers.

Examples:
- structured logger
- request tracing helpers
- Prometheus metrics emitters
- audit event emitters

### `packages/sdk`
Optional future SDK for competition authors or participants.

Examples:
- standard inference entrypoint
- submission manifest generator
- local validation CLI

## Docs layout

```text
docs/
  architecture/
  api/
  competition-authoring/
  operations/
  security/
  runbooks/
```

Keep docs near code for local details, but store product and architecture decisions in `docs/`.

## Tests layout

```text
tests/
  unit/
  integration/
  e2e/
  fixtures/
```

Recommended policy:
- unit tests for domain logic
- integration tests for DB, queue, storage, and execution boundaries
- end-to-end tests for submission lifecycle

## Suggested development workflow

### Local development
- Run web, api, postgres, redis, and minio with Docker Compose.
- Use one local worker process.
- Keep one sample competition and tiny dataset for smoke testing.

### CI
- lint
- type-check
- unit tests
- integration tests
- container build
- migration check

### CD
- deploy web and api
- deploy worker separately
- run migrations before or during rollout using controlled process

## Boundary rules

These rules help the project stay clean as it grows.

### The web app should not
- talk directly to the database
- contain scoring logic
- know how containers are executed

### The API should not
- run long jobs inline
- embed Docker execution details in route handlers
- directly compute heavy leaderboard recalculations in requests

### The worker should not
- own business rules for user permissions
- serve public HTTP endpoints
- decide competition policy on its own

### Shared packages should not
- depend on app-level router code
- contain hidden side effects
- mix domain logic with framework glue

## Naming conventions

- `competition` for the top-level challenge
- `phase` for stage-specific rules
- `submission` for one participant attempt
- `job` for one asynchronous execution task
- `artifact` for stored output/log/model files
- `score` for raw or final evaluated result
- `leaderboard_entry` for a projected ranking record

## Versioning rules you should enforce

Track these values explicitly:
- dataset version
- scoring version
- rules version
- runtime image digest
- submission manifest version

This will save you later when a participant asks why a score changed.

## Suggested first milestone repo setup

For the first month, keep it simple:

```text
competition-platform/
  apps/
    web/
    api/
    worker/
  packages/
    core/
    db/
    competitions/
    submissions/
    scoring/
    leaderboard/
    storage/
    execution/
  infra/
    docker/
    scripts/
  docs/
  tests/
```

Do not introduce Kubernetes-only folders too early unless you are actively deploying there.
