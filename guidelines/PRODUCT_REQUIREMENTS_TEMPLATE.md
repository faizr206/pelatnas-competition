# Product Requirements Template

## Goal
Describe what the competition platform feature or competition should achieve.

## Users
- participant
- admin

## Core user flows
- browse competition
- read rules
- download dataset
- submit CSV or notebook
- view score
- view leaderboard
- inspect logs and artifacts
- admin creates and manages competition

## Competition definition
- title
- description
- single phase timeline
- dataset versions
- allowed submission types: csv or jupyter notebook
- runtime limits
- scoring rule
- leaderboard visibility
- prizes or incentives if any
- old dataset versions remain visible
- admin-defined scoring metric

## Constraints
- max archive size
- max runtime
- max memory
- max daily submissions
- allowed frameworks

## Phase 1 defaults
- one admin makes the competition decisions
- participants submit only
- current leaderboard is used
- constraints should be configurable later, not hard-coded

## Success metrics
- successful submission completion rate
- average scoring latency
- leaderboard freshness
- infrastructure cost per submission
