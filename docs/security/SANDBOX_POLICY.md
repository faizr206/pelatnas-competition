# Sandbox Policy

Phase 0 does not execute user code yet, but the worker and execution package are locked to the agreed contract so Phase 2 does not drift.

## Locked limits

- run as non-root
- outbound internet disabled by default
- read-only dataset mount
- separate writable work directory
- 2 CPU limit
- 4 GB RAM limit
- 20 minute hard timeout
- approved base images only
- no user-provided Dockerfiles

## Worker expectations

- workers connect independently to Redis and pull jobs only when capacity is available
- execution policy stays outside HTTP handlers
- execution artifacts are written under local storage and can be collected later

## Deferred work

- Docker executor implementation
- stronger sandboxing
- GPU worker classes
- per-competition runtime images

