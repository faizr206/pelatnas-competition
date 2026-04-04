from pathlib import Path

from packages.scoring.service import compute_submission_score


def test_compute_submission_score_for_csv_row_count(tmp_path: Path) -> None:
    source = tmp_path / "submission.csv"
    source.write_text("prediction\n1\n2\n3\n", encoding="utf-8")

    metric_value, score_value = compute_submission_score(
        submission_type="csv",
        source_path=str(source),
        scoring_metric="row_count",
    )

    assert metric_value == 3.0
    assert score_value == 3.0


def test_compute_submission_score_for_notebook_code_submission(tmp_path: Path) -> None:
    source = tmp_path / "submission.ipynb"
    source.write_text(
        """
{
  "cells": [
    {
      "cell_type": "code",
      "metadata": {},
      "source": [
        "def predict(data):\\n",
        "    return data['value'] * 2\\n"
      ]
    }
  ],
  "metadata": {},
  "nbformat": 4,
  "nbformat_minor": 5
}
""".strip(),
        encoding="utf-8",
    )
    metric_script = tmp_path / "metric.py"
    metric_script.write_text(
        """
from participant_submission import predict

def score_submission():
    rows = [{"value": 1}, {"value": 3}, {"value": 5}]
    return sum(predict(row) for row in rows)
""".strip(),
        encoding="utf-8",
    )

    metric_value, score_value = compute_submission_score(
        submission_type="notebook",
        source_path=str(source),
        scoring_metric="code_submission_score",
        metric_script_path=str(metric_script),
        artifact_dir=str(tmp_path / "artifacts"),
    )

    assert metric_value == 18.0
    assert score_value == 18.0
    assert (tmp_path / "artifacts" / "participant_submission.py").exists()
