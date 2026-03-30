# Phase 1 Implementation Notes

This repository now implements the Phase 1 MVP competition flow on top of the Phase 0 foundation.

## Implemented scope

- admin competition CRUD with a single phase
- competition-level scoring and constraint settings
- dataset upload with version history and active-version marking
- CSV and notebook file submission upload
- worker-based validation, scoring, artifact generation, and leaderboard refresh
- participant views for submissions, scores, and leaderboard
- shadcn-style UI primitives for the web dashboard

## Scoring model

- scoring configuration lives on the competition record
- supported metrics are intentionally simple and deterministic for the MVP
- leaderboard entries are projected from persisted score rows, not computed ad hoc in the UI

## Retention model

- retention values live on the competition record
- cleanup work is exposed as a worker task skeleton and can be scheduled later
- source, log, and artifact deletion are kept separate from score and leaderboard persistence

