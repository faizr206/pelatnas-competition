from typing import Any

"""
Template: Mean Squared Error

Expected files:
- solution.csv must contain an "Id" column and a numeric "target" column
- submission.csv must contain an "Id" column and a numeric "prediction" column
"""

METRIC_NAME = "mse"
SCORING_DIRECTION = "min"


def score_submission(
    solution_rows: list[dict[str, Any]],
    submission_rows: list[dict[str, Any]],
) -> float:
    total_error = 0.0

    for solution_row, submission_row in zip(solution_rows, submission_rows, strict=False):
        target = float(solution_row["target"])
        prediction = float(submission_row["prediction"])
        total_error += (prediction - target) ** 2

    return total_error / len(solution_rows)
