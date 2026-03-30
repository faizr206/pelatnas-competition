from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

SUPPORTED_SCORING_METRICS = {
    "row_count",
    "numeric_sum",
    "mean_value",
    "file_size_kb",
    "notebook_code_cells",
    "checksum_mod_1000",
}


def compute_submission_score(
    *,
    submission_type: str,
    source_path: str,
    scoring_metric: str,
) -> tuple[float, float]:
    if scoring_metric not in SUPPORTED_SCORING_METRICS:
        raise ValueError(f"Unsupported scoring metric: {scoring_metric}")

    source = Path(source_path)
    if submission_type == "csv":
        metric_value = _score_csv(source=source, scoring_metric=scoring_metric)
    elif submission_type == "notebook":
        metric_value = _score_notebook(source=source, scoring_metric=scoring_metric)
    else:
        raise ValueError(f"Unsupported submission type: {submission_type}")

    return metric_value, metric_value


def _score_csv(*, source: Path, scoring_metric: str) -> float:
    if scoring_metric == "file_size_kb":
        return round(source.stat().st_size / 1024.0, 4)
    if scoring_metric == "checksum_mod_1000":
        return _checksum_mod_1000(source)

    with source.open("r", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    if scoring_metric == "row_count":
        return float(max(len(rows) - 1, 0))

    numeric_values: list[float] = []
    for row in rows[1:]:
        for value in row:
            try:
                numeric_values.append(float(value))
            except ValueError:
                continue

    if scoring_metric == "numeric_sum":
        return round(sum(numeric_values), 6)
    if scoring_metric == "mean_value":
        if not numeric_values:
            return 0.0
        return round(sum(numeric_values) / len(numeric_values), 6)
    if scoring_metric == "notebook_code_cells":
        return 0.0

    raise ValueError(f"Unsupported CSV metric: {scoring_metric}")


def _score_notebook(*, source: Path, scoring_metric: str) -> float:
    if scoring_metric == "file_size_kb":
        return round(source.stat().st_size / 1024.0, 4)
    if scoring_metric == "checksum_mod_1000":
        return _checksum_mod_1000(source)

    with source.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    cells = payload.get("cells", [])
    code_cells = [cell for cell in cells if cell.get("cell_type") == "code"]

    if scoring_metric == "notebook_code_cells":
        return float(len(code_cells))
    if scoring_metric == "row_count":
        return float(len(cells))
    if scoring_metric == "numeric_sum":
        return float(sum(len("".join(cell.get("source", []))) for cell in code_cells))
    if scoring_metric == "mean_value":
        if not code_cells:
            return 0.0
        return round(
            sum(len("".join(cell.get("source", []))) for cell in code_cells) / len(code_cells),
            6,
        )

    raise ValueError(f"Unsupported notebook metric: {scoring_metric}")


def _checksum_mod_1000(source: Path) -> float:
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    return round((int(digest[:10], 16) % 1000) / 10.0, 6)
