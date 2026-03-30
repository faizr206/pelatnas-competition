# Security Checklist

## Application
- enforce auth on all private routes
- validate upload size and file type
- rate-limit submission endpoints
- scan uploaded archives
- sign artifact URLs
- audit admin actions

## Execution
- disable network by default
- run as non-root
- remove unnecessary Linux capabilities
- enforce CPU and memory limits
- enforce timeout
- isolate filesystem access
- delete temp workspaces

## Secrets
- keep secrets out of source code
- use secret manager or environment injection
- rotate credentials
- separate staging and production secrets

## Data
- version datasets
- checksum all important files
- control access to private test sets
- never expose hidden labels

## Operations
- backup postgres
- backup metadata for object storage
- have incident runbooks
- log job failures with enough context
