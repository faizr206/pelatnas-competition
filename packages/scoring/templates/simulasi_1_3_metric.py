"""Metric for notebook submissions on the linear-regression classification task."""

import csv
from pathlib import Path

import competition_solution
from participant_submission import LINE_PARAMS, predict_from_params

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    np = None

try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    pd = None

TEMPLATE_TITLE = "simulasi 1.3 metric"
METRIC_NAME = "accuracy_div_num_lines"
SCORING_DIRECTION = "max"


def _test_csv_path() -> Path:
    path = Path(__file__).with_name("test.csv")
    if not path.exists():
        raise ValueError("Upload test.csv before using this metric.")
    return path


def _load_joined_rows(usage: str):
    solution_path = competition_solution.PATH
    if not solution_path:
        raise ValueError("Upload solution.csv before using this metric.")

    test_path = _test_csv_path()

    if pd is not None:
        test_df = pd.read_csv(test_path)
        solution_df = pd.read_csv(solution_path)
        if test_df.empty:
            raise ValueError("test.csv must contain at least one row.")
        if solution_df.empty:
            raise ValueError("solution.csv must contain at least one row.")
        if "Usage" not in solution_df.columns:
            raise ValueError("solution.csv must contain a Usage column.")

        scoped_solution_df = solution_df[
            solution_df["Usage"].astype(str).str.lower() == usage.lower()
        ]
        if scoped_solution_df.empty:
            raise ValueError(f"solution.csv must contain at least one {usage} row.")

        merged = test_df.merge(scoped_solution_df[["Id", "Class"]], on="Id", how="inner")
        if len(merged) != len(scoped_solution_df):
            raise ValueError(f"{usage} Id values in solution.csv must match rows in test.csv.")
        return merged

    with open(test_path, "r", encoding="utf-8", newline="") as handle:
        test_rows = list(csv.DictReader(handle))
    with open(solution_path, "r", encoding="utf-8", newline="") as handle:
        solution_rows = list(csv.DictReader(handle))

    if not test_rows:
        raise ValueError("test.csv must contain at least one row.")
    if not solution_rows:
        raise ValueError("solution.csv must contain at least one row.")

    test_by_id = {row["Id"]: row for row in test_rows}
    merged_rows = []
    filtered_solution_rows = [
        row for row in solution_rows if row.get("Usage", "").strip().lower() == usage.lower()
    ]
    if not filtered_solution_rows:
        raise ValueError(f"solution.csv must contain at least one {usage} row.")
    for row in filtered_solution_rows:
        test_row = test_by_id.get(row["Id"])
        if test_row is None:
            raise ValueError(f"{usage} Id values in solution.csv must match rows in test.csv.")
        merged_rows.append(
            {
                "Id": row["Id"],
                "x1": float(test_row["x1"]),
                "x2": float(test_row["x2"]),
                "Class": int(row["Class"]),
            }
        )
    return merged_rows


def _score_for_usage(usage: str, num_lines: int) -> float:
    rows = _load_joined_rows(usage)

    if pd is not None and hasattr(rows, "to_numpy"):
        x_values = rows[["x1", "x2"]].to_numpy(dtype=float)
        y_true = rows["Class"].to_numpy(dtype=int)
    elif np is not None:
        x_values = np.asarray([[row["x1"], row["x2"]] for row in rows], dtype=float)
        y_true = np.asarray([row["Class"] for row in rows], dtype=int)
    else:
        x_values = [[float(row["x1"]), float(row["x2"])] for row in rows]
        y_true = [int(row["Class"]) for row in rows]

    y_pred = predict_from_params(x_values, LINE_PARAMS)
    if len(y_pred) != len(y_true):
        raise ValueError("predict_from_params must return one label per test row.")

    correct = 0
    for pred, true in zip(y_pred, y_true, strict=False):
        pred_int = int(pred)
        if not 0 <= pred_int <= 9:
            raise ValueError("Predicted labels must be integers in 0..9.")
        if pred_int == int(true):
            correct += 1

    accuracy = correct / len(y_true)
    return accuracy / num_lines


def score_submission():
    if not isinstance(LINE_PARAMS, list) or not LINE_PARAMS:
        raise ValueError("participant_submission.LINE_PARAMS must be a non-empty list.")

    num_lines = len(LINE_PARAMS)
    public_score = _score_for_usage("Public", num_lines)
    private_score = _score_for_usage("Private", num_lines)
    return {
        "metric_value": private_score,
        "score_value": private_score,
        "public_score_value": public_score,
        "private_score_value": private_score,
    }
