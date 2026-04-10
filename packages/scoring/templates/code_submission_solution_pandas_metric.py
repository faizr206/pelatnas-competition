"""Template for notebook submissions scored against judge-uploaded solution.csv."""

import csv

import competition_solution
from participant_submission import predict

try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    pd = None

METRIC_NAME = "code_submission_solution_score"
SCORING_DIRECTION = "max"


def score_submission() -> float:
    if not competition_solution.PATH:
        raise ValueError("Upload solution.csv before using this metric template.")

    if pd is not None:
        solution_df = pd.read_csv(competition_solution.PATH)
        if solution_df.empty:
            raise ValueError("solution.csv must contain at least one row.")
        rows = solution_df.to_dict(orient="records")
    else:
        with open(competition_solution.PATH, encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError("solution.csv must contain at least one row.")

    correct = 0
    for row in rows:
        if predict({"value": int(row["value"])}) == int(row["expected"]):
            correct += 1

    return correct / len(rows)
