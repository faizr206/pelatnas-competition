"""Example template for notebook-based code submissions."""

from participant_submission import predict

METRIC_NAME = "code_submission_score"
SCORING_DIRECTION = "max"


def score_submission() -> float:
    evaluation_rows = [
        {"features": {"value": 1}, "expected": 2},
        {"features": {"value": 2}, "expected": 4},
    ]
    correct = 0
    for row in evaluation_rows:
        if predict(row["features"]) == row["expected"]:
            correct += 1
    return correct / len(evaluation_rows)
