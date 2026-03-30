# Execution Sandbox

This is the highest-risk part of the platform.

## Goals

- run untrusted code safely
- enforce fair resource usage
- produce reproducible results
- isolate tenants from each other

## Minimum controls for v1

- run as non-root
- read-only dataset mount
- separate writable work directory
- no outbound network by default
- CPU limit
- memory limit
- disk limit where possible
- hard timeout
- process cleanup after completion
- capability dropping
- minimal trusted base images only

## Do not allow in early versions

- arbitrary user-provided Dockerfiles
- privileged containers
- host mounts beyond controlled volumes
- unrestricted internet access
- shared writable dataset mounts

## Suggested runtime contract

Require the submission to include:
- a manifest file
- an entrypoint command
- dependency declaration
- output contract

Example output contract:
- `predictions.csv`
- `metrics.json`
- `manifest_out.json`
- `stdout.log`

## Suggested execution flow

1. download archive
2. validate manifest
3. unpack into temp dir
4. mount dataset read-only
5. run entrypoint
6. stream logs
7. collect outputs
8. validate outputs
9. destroy environment

## Future improvements

- gVisor or stronger sandboxing
- Kubernetes Jobs
- CPU and GPU execution classes
- per-competition base images
- malware scanning
