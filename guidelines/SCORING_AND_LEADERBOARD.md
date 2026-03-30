# Scoring and Leaderboard

## Scoring principles

- scoring must be deterministic when possible
- scoring policy must be versioned
- final displayed ranking should come from persisted score records
- never trust self-reported metrics if you can recompute them

## Submission types

### File submission
Score based on output file only.

### Code submission
Score based on execution result and generated outputs.

### Model-aware submission
Score can include:
- prediction quality
- parameter count
- FLOPs
- latency
- memory footprint
- architecture compliance

## Example score formula

```text
final_score = primary_metric - complexity_penalty - latency_penalty
```

## Leaderboard rules

Define clearly:
- whether only best submission counts
- whether competition admins can adjust best-submission selection rules
- tie-break policy, with submission time as the default tie-breaker
- daily submission caps
- private/public split
- freeze behavior after competition end
- team merge rules if teams are supported

## Projection model

Use:
- raw score records
- best-submission selection logic
- materialized leaderboard table

Do not compute rankings from scratch on every request.
