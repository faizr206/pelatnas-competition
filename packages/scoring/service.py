from __future__ import annotations

import contextlib
import csv
import hashlib
import importlib.util
import json
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

SUPPORTED_SCORING_METRICS = {
    "row_count",
    "numeric_sum",
    "mean_value",
    "file_size_kb",
    "notebook_code_cells",
    "checksum_mod_1000",
}

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
PARTICIPANT_MODULE_NAME = "participant_submission"


@dataclass(frozen=True)
class MetricTemplate:
    name: str
    title: str
    description: str
    code: str
    default_metric_name: str
    default_scoring_direction: str


def compute_submission_score(
    *,
    submission_type: str,
    source_path: str,
    scoring_metric: str,
    solution_path: str | None = None,
    metric_script_path: str | None = None,
    artifact_dir: str | None = None,
) -> tuple[float, float]:
    if metric_script_path and (submission_type == "notebook" or solution_path):
        return _score_with_custom_metric(
            submission_type=submission_type,
            source_path=source_path,
            solution_path=solution_path,
            metric_script_path=metric_script_path,
            artifact_dir=artifact_dir,
        )
    if solution_path and not metric_script_path:
        raise ValueError("Competition scoring is incomplete. Save the metric script.")
    if metric_script_path and submission_type == "csv" and not solution_path:
        raise ValueError(
            "Competition scoring is incomplete. Save both solution.csv and the metric script."
        )

    if scoring_metric not in SUPPORTED_SCORING_METRICS:
        raise ValueError(
            "Unsupported scoring metric. Configure and save both solution.csv and a custom "
            "metric script for this competition."
        )

    source = Path(source_path)
    if submission_type == "csv":
        metric_value = _score_csv(source=source, scoring_metric=scoring_metric)
    elif submission_type == "notebook":
        metric_value = _score_notebook(source=source, scoring_metric=scoring_metric)
    else:
        raise ValueError(f"Unsupported submission type: {submission_type}")

    return metric_value, metric_value


def list_metric_templates() -> list[MetricTemplate]:
    templates: list[MetricTemplate] = []

    for path in sorted(TEMPLATES_DIR.glob("*.py")):
        module = _load_metric_module(path, participant_module=_build_stub_participant_module())
        templates.append(
            MetricTemplate(
                name=path.stem,
                title=path.stem.replace("_", " ").title(),
                description=(module.__doc__ or "Scoring template").strip(),
                code=path.read_text(encoding="utf-8"),
                default_metric_name=str(getattr(module, "METRIC_NAME", path.stem)),
                default_scoring_direction=str(getattr(module, "SCORING_DIRECTION", "min")),
            )
        )

    return templates


def validate_solution_csv(path: str) -> None:
    rows = _read_csv_rows(Path(path))
    if not rows:
        raise ValueError("solution.csv must contain at least one row.")


def validate_metric_script(path: str, *, submission_mode: str = "prediction_file") -> None:
    participant_module = (
        _build_stub_participant_module() if submission_mode == "code_submission" else None
    )
    _load_metric_module(Path(path), participant_module=participant_module)


def _score_with_custom_metric(
    *,
    submission_type: str,
    source_path: str,
    solution_path: str | None,
    metric_script_path: str,
    artifact_dir: str | None,
) -> tuple[float, float]:
    if submission_type == "csv":
        if solution_path is None:
            raise ValueError(
                "Competition scoring is incomplete. Save both solution.csv and the metric script."
            )
        solution_rows = _read_csv_rows(Path(solution_path))
        submission_rows = _read_csv_rows(Path(source_path))
        aligned_solution_rows, aligned_submission_rows = _align_rows_by_id(
            solution_rows=solution_rows,
            submission_rows=submission_rows,
        )

        module = _load_metric_module(Path(metric_script_path))
        raw_score = module.score_submission(aligned_solution_rows, aligned_submission_rows)
        if not isinstance(raw_score, int | float):
            raise ValueError("score_submission must return a numeric score.")

        score = float(raw_score)
        return score, score

    if submission_type == "notebook":
        if artifact_dir is None:
            raise ValueError("Notebook scoring requires an artifact directory.")
        return _score_notebook_with_custom_metric(
            source_path=source_path,
            metric_script_path=metric_script_path,
            artifact_dir=artifact_dir,
        )

    raise ValueError(f"Unsupported submission type: {submission_type}")


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        if "Id" not in fieldnames:
            raise ValueError(f"{path.name} must contain an Id column.")
        rows = list(reader)

    ids = [row.get("Id", "").strip() for row in rows]
    if any(not value for value in ids):
        raise ValueError(f"{path.name} contains blank Id values.")
    if len(set(ids)) != len(ids):
        raise ValueError(f"{path.name} contains duplicate Id values.")

    return rows


def _align_rows_by_id(
    *,
    solution_rows: list[dict[str, str]],
    submission_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    solution_by_id = {row["Id"]: row for row in solution_rows}
    submission_by_id = {row["Id"]: row for row in submission_rows}

    if set(solution_by_id) != set(submission_by_id):
        missing = sorted(set(solution_by_id) - set(submission_by_id))
        unexpected = sorted(set(submission_by_id) - set(solution_by_id))
        details: list[str] = []
        if missing:
            details.append(f"missing Ids: {', '.join(missing[:5])}")
        if unexpected:
            details.append(f"unexpected Ids: {', '.join(unexpected[:5])}")
        raise ValueError("Submission Id values do not match solution.csv. " + "; ".join(details))

    ordered_ids = [row["Id"] for row in solution_rows]
    return (
        [solution_by_id[item_id] for item_id in ordered_ids],
        [submission_by_id[item_id] for item_id in ordered_ids],
    )


def _score_notebook_with_custom_metric(
    *,
    source_path: str,
    metric_script_path: str,
    artifact_dir: str,
) -> tuple[float, float]:
    target_path = Path(artifact_dir) / f"{PARTICIPANT_MODULE_NAME}.py"
    _convert_notebook_to_python(source=Path(source_path), target_path=target_path)

    participant_module = _load_python_module(
        target_path,
        module_name=PARTICIPANT_MODULE_NAME,
    )
    predict = getattr(participant_module, "predict", None)
    if not callable(predict):
        raise ValueError("Notebook submission must define a callable predict function.")

    metric_module = _load_metric_module(
        Path(metric_script_path),
        participant_module=participant_module,
    )
    raw_score = metric_module.score_submission()
    if not isinstance(raw_score, int | float):
        raise ValueError("score_submission must return a numeric score.")

    score = float(raw_score)
    return score, score


def _load_metric_module(
    path: Path,
    *,
    participant_module: ModuleType | None = None,
) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        f"competition_metric_{hashlib.sha256(str(path).encode()).hexdigest()[:12]}",
        path,
    )
    if spec is None or spec.loader is None:
        raise ValueError("Metric script could not be loaded.")

    module = importlib.util.module_from_spec(spec)
    with _temporary_participant_module(participant_module):
        spec.loader.exec_module(module)

    score_submission = getattr(module, "score_submission", None)
    if not callable(score_submission):
        raise ValueError("Metric script must define a callable score_submission function.")

    return module


def _load_python_module(path: Path, *, module_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"{path.name} could not be loaded.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _convert_notebook_to_python(*, source: Path, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with source.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    lines: list[str] = []
    for index, cell in enumerate(payload.get("cells", []), start=1):
        if cell.get("cell_type") != "code":
            continue

        if lines:
            lines.append("")
        lines.append(f"# Cell {index}")

        source_value = cell.get("source", [])
        if isinstance(source_value, str):
            cell_source = source_value
        else:
            cell_source = "".join(source_value)
        lines.append(cell_source.rstrip("\n"))

    target_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _build_stub_participant_module() -> ModuleType:
    module = ModuleType(PARTICIPANT_MODULE_NAME)

    def predict(_data: object) -> None:
        return None

    module.predict = predict  # type: ignore[attr-defined]
    return module


@contextlib.contextmanager
def _temporary_participant_module(
    participant_module: ModuleType | None,
) -> Iterator[None]:
    if participant_module is None:
        yield
        return

    original = sys.modules.get(PARTICIPANT_MODULE_NAME)
    sys.modules[PARTICIPANT_MODULE_NAME] = participant_module
    try:
        yield
    finally:
        if original is None:
            sys.modules.pop(PARTICIPANT_MODULE_NAME, None)
        else:
            sys.modules[PARTICIPANT_MODULE_NAME] = original


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
