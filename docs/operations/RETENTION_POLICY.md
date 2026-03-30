# Retention Policy

Phase 1 keeps retention policy explicit and competition-driven, while cleanup scheduling remains a worker concern.

## Default policy

- datasets: permanent
- scores: permanent
- submission source: 30 days
- logs: 14 days
- artifacts: 14 days
- best submissions: permanent

## Implementation status

- retention values are stored on each competition record
- the worker exposes a `retention.cleanup` task skeleton
- the cleanup task can remove expired source files, logs, and artifacts
- scheduling and production-grade safety checks can be added later

## Deferred hardening

- dry-run mode
- deletion audit events
- object-storage lifecycle integration
- admin-triggered cleanup history
