# Architecture

## Recommended architecture style

Start with a modular monolith for product logic and a separate worker tier for background execution.

Why:
- easier to build
- easier to debug
- lower operational complexity
- still compatible with later scaling

## Main components

### 1. Web frontend
Responsibilities:
- sign-in
- competition browsing
- submission flow
- leaderboard views
- admin dashboards

### 2. API service
Responsibilities:
- business logic
- auth
- metadata persistence
- job creation
- score and leaderboard APIs

### 3. PostgreSQL
Stores:
- users
- teams
- competitions
- datasets
- submissions
- jobs
- scores
- leaderboard projections
- audit logs

### 4. Storage
Stores:
- local disk for v1
- datasets
- starter kits
- submission archives
- output artifacts
- execution logs
- model files

Later:
- move to S3-compatible storage when local disk becomes limiting

### 5. Queue
Used for:
- execution jobs
- scoring jobs
- leaderboard refresh jobs
- cleanup jobs

### 6. Worker/executor
Runs:
- code submissions
- artifact collection
- scoring pipelines
- leaderboard updates

## Submission lifecycle

1. User uploads submission
2. API validates metadata
3. Files are stored on local disk
4. API creates submission + job record
5. Worker picks job
6. Worker creates isolated runtime
7. Dataset mounted read-only
8. Entrypoint runs
9. Outputs collected
10. Scorer computes final score
11. Score is persisted
12. Leaderboard projection is updated

## Scaling path

### Stage 1
- One API service
- One database
- One Redis
- One worker machine

### Stage 2
- Multiple API replicas
- Separate worker nodes
- Managed database
- Managed object storage

### Stage 3
- Kubernetes Jobs for execution
- CPU and GPU worker pools
- autoscaling
- per-competition execution profiles

## Non-functional requirements

- reproducibility
- fairness
- secure code execution
- auditability
- cost control
- operational simplicity
