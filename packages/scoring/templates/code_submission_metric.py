"""Example template for notebook-based code submissions."""

from participant_submission import predict
import competition_solution

METRIC_NAME = "code_submission_score"
SCORING_DIRECTION = "max"


def score_submission() -> float:
    evaluation_rows = competition_solution.read_rows() or [
        {"Id": "1", "value": "1", "expected": "2"},
        {"Id": "2", "value": "2", "expected": "4"},
    ]
    correct = 0
    for row in evaluation_rows:
        features = {"value": int(row["value"])}
        if predict(features) == int(row["expected"]):
            correct += 1
    return correct / len(evaluation_rows)
