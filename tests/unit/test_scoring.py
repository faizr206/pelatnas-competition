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
