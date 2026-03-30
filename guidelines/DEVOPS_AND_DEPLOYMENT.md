# DevOps and Deployment

## Environments

- local
- staging
- production

## Local setup
Use Docker Compose for:
- web
- api
- worker
- postgres
- redis
- local storage volume

## CI pipeline

Recommended checks:
- formatting
- lint
- type checks
- unit tests
- integration tests
- migration validation
- container image build

## Production deployment

### Early stage
- VPS or small cloud instances
- one db instance
- one redis instance
- one object storage bucket
- one worker node

### Later stage
- managed postgres
- managed redis
- managed object storage
- multiple worker pools
- kubernetes for executor jobs

## Observability

You need:
- structured logs
- request IDs
- job IDs in every log line
- metrics
- alerts
- dashboards

Track at minimum:
- queue depth
- job latency
- submission success rate
- worker utilization
- leaderboard refresh latency
