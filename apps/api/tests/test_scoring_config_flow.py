import json
from io import BytesIO

from apps.worker.worker.job_handlers.submission_pipeline import process_submission_job


class DummyAsyncResult:
    id = "task-test-456"


def _login_admin(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin1234"},
    )
    assert response.status_code == 200


def test_custom_scoring_config_scores_submission_against_solution(client, monkeypatch) -> None:
    _login_admin(client)

    create_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "scored-comp",
            "title": "Scored Competition",
            "description": "Competition with solution based scoring",
            "visibility": "public",
            "status": "active",
            "scoring_metric": "mse",
            "scoring_direction": "min",
            "best_submission_rule": "best_score",
            "max_submissions_per_day": 5,
            "max_runtime_minutes": 20,
            "max_memory_mb": 4096,
            "max_cpu": 2,
            "allow_csv_submissions": True,
            "allow_notebook_submissions": False,
            "source_retention_days": 30,
            "log_retention_days": 14,
            "artifact_retention_days": 14,
            "phase": {
                "name": "main",
                "starts_at": "2026-01-01T00:00:00Z",
                "ends_at": "2099-12-31T00:00:00Z",
                "submission_limit_per_day": 5,
                "scoring_version": "v1",
                "rules_version": "v1",
            },
        },
    )
    assert create_response.status_code == 201

    scoring_response = client.put(
        "/api/v1/competitions/scored-comp/scoring-config",
        data={
            "metric_name": "mse",
            "scoring_direction": "min",
            "metric_code": """
METRIC_NAME = "mse"
SCORING_DIRECTION = "min"

def score_submission(solution_rows, submission_rows):
    total = 0.0
    for solution_row, submission_row in zip(solution_rows, submission_rows):
        target = float(solution_row["target"])
        prediction = float(submission_row["prediction"])
        total += (prediction - target) ** 2
    return total / len(solution_rows)
""".strip(),
        },
        files={
            "solution_file": (
                "solution.csv",
                BytesIO(b"Id,target,Usage\n1,1.0,Public\n2,2.0,Private\n"),
                "text/csv",
            )
        },
    )
    assert scoring_response.status_code == 200
    scoring_payload = scoring_response.json()
    assert scoring_payload["solution_filename"] == "solution.csv"
    assert scoring_payload["metric_script_filename"] == "custom_metric.py"
    assert len(scoring_payload["templates"]) >= 1

    from apps.worker.worker import queue as worker_queue

    monkeypatch.setattr(
        worker_queue.process_submission_task,
        "apply_async",
        lambda args: DummyAsyncResult(),
    )

    submission_response = client.post(
        "/api/v1/competitions/scored-comp/submissions",
        data={"submission_type": "csv"},
        files={
            "source_file": (
                "submission.csv",
                BytesIO(b"Id,prediction\n1,1.5\n2,1.0\n"),
                "text/csv",
            )
        },
    )
    assert submission_response.status_code == 202
    job_id = submission_response.json()["id"]

    process_submission_job(job_id)

    submissions_response = client.get("/api/v1/competitions/scored-comp/submissions")
    assert submissions_response.status_code == 200
    submission_payload = submissions_response.json()[0]
    assert submission_payload["latest_score"]["metric_name"] == "mse"
    assert submission_payload["latest_score"]["score_value"] == 0.25
    assert submission_payload["latest_score"]["public_score_value"] == 0.25
    assert submission_payload["latest_score"]["private_score_value"] == 1.0

    private_leaderboard_response = client.get(
        "/api/v1/competitions/scored-comp/leaderboard/private"
    )
    assert private_leaderboard_response.status_code == 404


def test_scoring_config_requires_solution_file_on_first_save(client) -> None:
    _login_admin(client)

    create_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "missing-solution-comp",
            "title": "Missing Solution Competition",
            "description": "Competition without solution upload",
            "visibility": "public",
            "status": "active",
            "scoring_metric": "mse",
            "scoring_direction": "min",
            "best_submission_rule": "best_score",
            "max_submissions_per_day": 5,
            "max_runtime_minutes": 20,
            "max_memory_mb": 4096,
            "max_cpu": 2,
            "allow_csv_submissions": True,
            "allow_notebook_submissions": False,
            "source_retention_days": 30,
            "log_retention_days": 14,
            "artifact_retention_days": 14,
            "phase": {
                "name": "main",
                "starts_at": "2026-01-01T00:00:00Z",
                "ends_at": "2026-12-31T00:00:00Z",
                "submission_limit_per_day": 5,
                "scoring_version": "v1",
                "rules_version": "v1",
            },
        },
    )
    assert create_response.status_code == 201

    scoring_response = client.put(
        "/api/v1/competitions/missing-solution-comp/scoring-config",
        data={
            "metric_name": "mse",
            "scoring_direction": "min",
            "metric_code": """
def score_submission(solution_rows, submission_rows):
    return 0.0
""".strip(),
        },
    )
    assert scoring_response.status_code == 400
    assert scoring_response.json()["detail"] == (
        "Upload solution.csv before saving scoring configuration."
    )


def test_code_submission_competition_scores_uploaded_notebook(client, monkeypatch) -> None:
    _login_admin(client)

    create_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "code-comp",
            "title": "Code Competition",
            "description": "Competition with notebook code submissions",
            "visibility": "public",
            "status": "active",
            "submission_mode": "code_submission",
            "scoring_metric": "code_submission_score",
            "scoring_direction": "max",
            "best_submission_rule": "best_score",
            "max_submissions_per_day": 5,
            "max_runtime_minutes": 20,
            "max_memory_mb": 4096,
            "max_cpu": 2,
            "allow_csv_submissions": False,
            "allow_notebook_submissions": True,
            "source_retention_days": 30,
            "log_retention_days": 14,
            "artifact_retention_days": 14,
            "phase": {
                "name": "main",
                "starts_at": "2026-01-01T00:00:00Z",
                "ends_at": "2026-12-31T00:00:00Z",
                "submission_limit_per_day": 5,
                "scoring_version": "v1",
                "rules_version": "v1",
            },
        },
    )
    assert create_response.status_code == 201

    scoring_response = client.put(
        "/api/v1/competitions/code-comp/scoring-config",
        data={
            "metric_name": "code_submission_score",
            "scoring_direction": "max",
            "metric_code": """
from participant_submission import predict

def score_submission():
    rows = [
        {"features": {"value": 2}, "expected": 4},
        {"features": {"value": 5}, "expected": 10},
    ]
    return sum(
        1.0
        for row in rows
        if predict(row["features"]) == row["expected"]
    )
""".strip(),
        },
    )
    assert scoring_response.status_code == 200
    assert scoring_response.json()["submission_mode"] == "code_submission"
    assert scoring_response.json()["solution_filename"] is None

    from apps.worker.worker import queue as worker_queue

    monkeypatch.setattr(
        worker_queue.process_submission_task,
        "apply_async",
        lambda args: DummyAsyncResult(),
    )

    notebook_payload = json.dumps(
        {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": [
                        "def predict(data):\n",
                        "    return data['value'] * 2\n",
                    ],
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
    ).encode("utf-8")

    submission_response = client.post(
        "/api/v1/competitions/code-comp/submissions",
        data={"submission_type": "notebook"},
        files={
            "source_file": (
                "submission.ipynb",
                BytesIO(notebook_payload),
                "application/x-ipynb+json",
            )
        },
    )
    assert submission_response.status_code == 202
    job_id = submission_response.json()["id"]

    process_submission_job(job_id)

    submissions_response = client.get("/api/v1/competitions/code-comp/submissions")
    assert submissions_response.status_code == 200
    submission_payload = submissions_response.json()[0]
    assert submission_payload["latest_score"]["metric_name"] == "code_submission_score"
    assert submission_payload["latest_score"]["score_value"] == 2.0

    artifacts_response = client.get(f"/api/v1/submissions/{submission_payload['id']}/artifacts")
    assert artifacts_response.status_code == 200
    artifact_types = {item["artifact_type"] for item in artifacts_response.json()}
    assert "participant_submission.py" in artifact_types


def test_code_submission_metric_can_import_uploaded_solution_csv(client, monkeypatch) -> None:
    _login_admin(client)

    create_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "code-solution-comp",
            "title": "Code Solution Competition",
            "description": "Notebook competition with judge uploaded solution data",
            "visibility": "public",
            "status": "active",
            "submission_mode": "code_submission",
            "scoring_metric": "code_submission_score",
            "scoring_direction": "max",
            "best_submission_rule": "best_score",
            "max_submissions_per_day": 5,
            "max_runtime_minutes": 20,
            "max_memory_mb": 4096,
            "max_cpu": 2,
            "allow_csv_submissions": False,
            "allow_notebook_submissions": True,
            "source_retention_days": 30,
            "log_retention_days": 14,
            "artifact_retention_days": 14,
            "phase": {
                "name": "main",
                "starts_at": "2026-01-01T00:00:00Z",
                "ends_at": "2026-12-31T00:00:00Z",
                "submission_limit_per_day": 5,
                "scoring_version": "v1",
                "rules_version": "v1",
            },
        },
    )
    assert create_response.status_code == 201

    scoring_response = client.put(
        "/api/v1/competitions/code-solution-comp/scoring-config",
        data={
            "metric_name": "code_submission_score",
            "scoring_direction": "max",
            "metric_code": """
from participant_submission import predict
import competition_solution

def score_submission():
    rows = competition_solution.read_rows()
    return sum(
        1.0
        for row in rows
        if predict({"value": int(row["value"])}) == int(row["expected"])
    )
""".strip(),
        },
        files={
            "solution_file": (
                "solution.csv",
                BytesIO(b"Id,value,expected\n1,2,4\n2,5,10\n"),
                "text/csv",
            )
        },
    )
    assert scoring_response.status_code == 200
    assert scoring_response.json()["solution_filename"] == "solution.csv"

    from apps.worker.worker import queue as worker_queue

    monkeypatch.setattr(
        worker_queue.process_submission_task,
        "apply_async",
        lambda args: DummyAsyncResult(),
    )

    notebook_payload = json.dumps(
        {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": [
                        "def predict(data):\n",
                        "    return data['value'] * 2\n",
                    ],
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
    ).encode("utf-8")

    submission_response = client.post(
        "/api/v1/competitions/code-solution-comp/submissions",
        data={"submission_type": "notebook"},
        files={
            "source_file": (
                "submission.ipynb",
                BytesIO(notebook_payload),
                "application/x-ipynb+json",
            )
        },
    )
    assert submission_response.status_code == 202

    process_submission_job(submission_response.json()["id"])

    submissions_response = client.get("/api/v1/competitions/code-solution-comp/submissions")
    assert submissions_response.status_code == 200
    submission_payload = submissions_response.json()[0]
    assert submission_payload["latest_score"]["score_value"] == 2.0


def test_code_submission_metric_can_import_line_params_and_read_test_csv(
    client, monkeypatch
) -> None:
    _login_admin(client)

    create_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "code-test-comp",
            "title": "Code Test Competition",
            "description": "Notebook competition with solution and test csv scoring assets",
            "visibility": "public",
            "status": "active",
            "submission_mode": "code_submission",
            "scoring_metric": "accuracy_div_num_lines",
            "scoring_direction": "max",
            "best_submission_rule": "best_score",
            "max_submissions_per_day": 5,
            "max_runtime_minutes": 20,
            "max_memory_mb": 4096,
            "max_cpu": 2,
            "allow_csv_submissions": False,
            "allow_notebook_submissions": True,
            "source_retention_days": 30,
            "log_retention_days": 14,
            "artifact_retention_days": 14,
            "phase": {
                "name": "main",
                "starts_at": "2026-01-01T00:00:00Z",
                "ends_at": "2026-12-31T00:00:00Z",
                "submission_limit_per_day": 5,
                "scoring_version": "v1",
                "rules_version": "v1",
            },
        },
    )
    assert create_response.status_code == 201

    scoring_response = client.put(
        "/api/v1/competitions/code-test-comp/scoring-config",
        data={
            "metric_name": "accuracy_div_num_lines",
            "scoring_direction": "max",
            "metric_code": """
import csv
from pathlib import Path

import competition_solution
from participant_submission import LINE_PARAMS, predict_from_params

def score_submission():
    solution_path = competition_solution.PATH
    if not solution_path:
        raise ValueError("Upload solution.csv before using this metric.")

    test_path = Path(__file__).with_name("test.csv")
    with open(test_path, "r", encoding="utf-8", newline="") as handle:
        test_rows = list(csv.DictReader(handle))
    with open(solution_path, "r", encoding="utf-8", newline="") as handle:
        solution_rows = list(csv.DictReader(handle))

    test_by_id = {row["Id"]: row for row in test_rows}
    labels = []
    features = []
    for row in solution_rows:
        joined = test_by_id[row["Id"]]
        features.append([float(joined["x1"]), float(joined["x2"])])
        labels.append(int(row["Class"]))

    predictions = predict_from_params(features, LINE_PARAMS)
    correct = sum(1 for prediction, label in zip(predictions, labels) if int(prediction) == label)
    return (correct / len(labels)) / len(LINE_PARAMS)
""".strip(),
        },
        files={
            "solution_file": (
                "solution.csv",
                BytesIO(b"Id,Class\n1,1\n2,0\n"),
                "text/csv",
            ),
            "test_file": (
                "test.csv",
                BytesIO(b"Id,x1,x2\n1,0.9,0.2\n2,0.1,0.2\n"),
                "text/csv",
            ),
        },
    )
    assert scoring_response.status_code == 200
    assert scoring_response.json()["solution_filename"] == "solution.csv"
    assert scoring_response.json()["test_filename"] == "test.csv"

    from apps.worker.worker import queue as worker_queue

    monkeypatch.setattr(
        worker_queue.process_submission_task,
        "apply_async",
        lambda args: DummyAsyncResult(),
    )

    notebook_payload = json.dumps(
        {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": [
                        "LINE_PARAMS = [{'threshold': 1.0}]\n",
                        "\n",
                        "def predict_from_params(rows, line_params):\n",
                        "    threshold = float(line_params[0]['threshold'])\n",
                        "    return [1 if float(x1) + float(x2) >= threshold else 0 for x1, x2 in rows]\n",
                    ],
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
    ).encode("utf-8")

    submission_response = client.post(
        "/api/v1/competitions/code-test-comp/submissions",
        data={"submission_type": "notebook"},
        files={
            "source_file": (
                "submission.ipynb",
                BytesIO(notebook_payload),
                "application/x-ipynb+json",
            )
        },
    )
    assert submission_response.status_code == 202

    process_submission_job(submission_response.json()["id"])

    submissions_response = client.get("/api/v1/competitions/code-test-comp/submissions")
    assert submissions_response.status_code == 200
    submission_payload = submissions_response.json()[0]
    assert submission_payload["latest_score"]["score_value"] == 1.0


def test_notebook_metric_can_split_public_and_private_scores_by_usage(client, monkeypatch) -> None:
    _login_admin(client)

    create_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "code-split-comp",
            "title": "Code Split Competition",
            "description": "Notebook competition with split public and private scores",
            "visibility": "public",
            "status": "active",
            "submission_mode": "code_submission",
            "scoring_metric": "accuracy_div_num_lines",
            "scoring_direction": "max",
            "best_submission_rule": "best_score",
            "max_submissions_per_day": 5,
            "max_runtime_minutes": 20,
            "max_memory_mb": 4096,
            "max_cpu": 2,
            "allow_csv_submissions": False,
            "allow_notebook_submissions": True,
            "source_retention_days": 30,
            "log_retention_days": 14,
            "artifact_retention_days": 14,
            "phase": {
                "name": "main",
                "starts_at": "2026-01-01T00:00:00Z",
                "ends_at": "2026-12-31T00:00:00Z",
                "submission_limit_per_day": 5,
                "scoring_version": "v1",
                "rules_version": "v1",
            },
        },
    )
    assert create_response.status_code == 201

    scoring_response = client.put(
        "/api/v1/competitions/code-split-comp/scoring-config",
        data={
            "metric_name": "accuracy_div_num_lines",
            "scoring_direction": "max",
            "metric_code": """
import csv
from pathlib import Path

import competition_solution
from participant_submission import LINE_PARAMS, predict_from_params

def _score_for_usage(usage):
    test_path = Path(__file__).with_name("test.csv")
    with open(test_path, "r", encoding="utf-8", newline="") as handle:
        test_rows = list(csv.DictReader(handle))
    with open(competition_solution.PATH, "r", encoding="utf-8", newline="") as handle:
        solution_rows = list(csv.DictReader(handle))

    scoped_rows = [row for row in solution_rows if row["Usage"].lower() == usage.lower()]
    test_by_id = {row["Id"]: row for row in test_rows}
    features = []
    labels = []
    for row in scoped_rows:
        joined = test_by_id[row["Id"]]
        features.append([float(joined["x1"]), float(joined["x2"])])
        labels.append(int(row["Class"]))

    predictions = predict_from_params(features, LINE_PARAMS)
    correct = sum(1 for prediction, label in zip(predictions, labels) if int(prediction) == label)
    return (correct / len(labels)) / len(LINE_PARAMS)

def score_submission():
    public_score = _score_for_usage("Public")
    private_score = _score_for_usage("Private")
    return {
        "metric_value": private_score,
        "score_value": private_score,
        "public_score_value": public_score,
        "private_score_value": private_score,
    }
""".strip(),
        },
        files={
            "solution_file": (
                "solution.csv",
                BytesIO(b"Id,Class,Usage\n1,1,Public\n2,0,Public\n3,1,Private\n4,0,Private\n"),
                "text/csv",
            ),
            "test_file": (
                "test.csv",
                BytesIO(b"Id,x1,x2\n1,0.8,0.4\n2,0.1,0.2\n3,0.2,0.1\n4,0.9,0.2\n"),
                "text/csv",
            ),
        },
    )
    assert scoring_response.status_code == 200

    from apps.worker.worker import queue as worker_queue

    monkeypatch.setattr(
        worker_queue.process_submission_task,
        "apply_async",
        lambda args: DummyAsyncResult(),
    )

    notebook_payload = json.dumps(
        {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": [
                        "LINE_PARAMS = [{'threshold': 1.0}]\n",
                        "\n",
                        "def predict_from_params(rows, line_params):\n",
                        "    threshold = float(line_params[0]['threshold'])\n",
                        "    return [1 if float(x1) + float(x2) >= threshold else 0 for x1, x2 in rows]\n",
                    ],
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
    ).encode("utf-8")

    submission_response = client.post(
        "/api/v1/competitions/code-split-comp/submissions",
        data={"submission_type": "notebook"},
        files={
            "source_file": (
                "submission.ipynb",
                BytesIO(notebook_payload),
                "application/x-ipynb+json",
            )
        },
    )
    assert submission_response.status_code == 202

    process_submission_job(submission_response.json()["id"])

    submissions_response = client.get("/api/v1/competitions/code-split-comp/submissions")
    assert submissions_response.status_code == 200
    submission_payload = submissions_response.json()[0]
    assert submission_payload["latest_score"]["public_score_value"] == 1.0
    assert submission_payload["latest_score"]["private_score_value"] == 0.0
    assert submission_payload["latest_score"]["score_value"] == 1.0


def test_admin_can_rescore_all_csv_submissions(client, monkeypatch) -> None:
    _login_admin(client)

    create_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "rescore-csv-comp",
            "title": "Rescore CSV Competition",
            "description": "Competition for rescoring csv submissions",
            "visibility": "public",
            "status": "active",
            "scoring_metric": "mse",
            "scoring_direction": "min",
            "best_submission_rule": "best_score",
            "max_submissions_per_day": 5,
            "max_runtime_minutes": 20,
            "max_memory_mb": 4096,
            "max_cpu": 2,
            "allow_csv_submissions": True,
            "allow_notebook_submissions": False,
            "source_retention_days": 30,
            "log_retention_days": 14,
            "artifact_retention_days": 14,
            "phase": {
                "name": "main",
                "starts_at": "2026-01-01T00:00:00Z",
                "ends_at": "2099-12-31T00:00:00Z",
                "submission_limit_per_day": 5,
                "scoring_version": "v1",
                "rules_version": "v1",
            },
        },
    )
    assert create_response.status_code == 201

    first_scoring_response = client.put(
        "/api/v1/competitions/rescore-csv-comp/scoring-config",
        data={
            "metric_name": "mse",
            "scoring_direction": "min",
            "metric_code": """
def score_submission(solution_rows, submission_rows):
    total = 0.0
    for solution_row, submission_row in zip(solution_rows, submission_rows):
        target = float(solution_row["target"])
        prediction = float(submission_row["prediction"])
        total += (prediction - target) ** 2
    return total / len(solution_rows)
""".strip(),
        },
        files={
            "solution_file": (
                "solution.csv",
                BytesIO(b"Id,target\n1,1.0\n2,2.0\n"),
                "text/csv",
            )
        },
    )
    assert first_scoring_response.status_code == 200

    from apps.worker.worker import queue as worker_queue

    monkeypatch.setattr(
        worker_queue.process_submission_task,
        "apply_async",
        lambda args: DummyAsyncResult(),
    )

    submission_response = client.post(
        "/api/v1/competitions/rescore-csv-comp/submissions",
        data={"submission_type": "csv"},
        files={
            "source_file": (
                "submission.csv",
                BytesIO(b"Id,prediction\n1,1.5\n2,1.0\n"),
                "text/csv",
            )
        },
    )
    assert submission_response.status_code == 202
    process_submission_job(submission_response.json()["id"])

    updated_scoring_response = client.put(
        "/api/v1/competitions/rescore-csv-comp/scoring-config",
        data={
            "metric_name": "mae",
            "scoring_direction": "min",
            "metric_code": """
def score_submission(solution_rows, submission_rows):
    total = 0.0
    for solution_row, submission_row in zip(solution_rows, submission_rows):
        target = float(solution_row["target"])
        prediction = float(submission_row["prediction"])
        total += abs(prediction - target)
    return total / len(solution_rows)
""".strip(),
        },
        files={
            "solution_file": (
                "solution.csv",
                BytesIO(b"Id,target\n1,0.0\n2,0.0\n"),
                "text/csv",
            )
        },
    )
    assert updated_scoring_response.status_code == 200

    rescore_response = client.post("/api/v1/competitions/rescore-csv-comp/rescore-submissions")
    assert rescore_response.status_code == 200
    payload = rescore_response.json()
    assert payload["queued_submission_count"] == 1
    assert len(payload["job_ids"]) == 1

    process_submission_job(payload["job_ids"][0])

    submissions_response = client.get("/api/v1/competitions/rescore-csv-comp/submissions")
    assert submissions_response.status_code == 200
    submission_payload = submissions_response.json()[0]
    assert submission_payload["latest_score"]["metric_name"] == "mae"
    assert submission_payload["latest_score"]["public_score_value"] == 1.25


def test_admin_can_rescore_all_notebook_submissions(client, monkeypatch) -> None:
    _login_admin(client)

    create_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "rescore-code-comp",
            "title": "Rescore Code Competition",
            "description": "Competition for rescoring notebook submissions",
            "visibility": "public",
            "status": "active",
            "submission_mode": "code_submission",
            "scoring_metric": "code_submission_score",
            "scoring_direction": "max",
            "best_submission_rule": "best_score",
            "max_submissions_per_day": 5,
            "max_runtime_minutes": 20,
            "max_memory_mb": 4096,
            "max_cpu": 2,
            "allow_csv_submissions": False,
            "allow_notebook_submissions": True,
            "source_retention_days": 30,
            "log_retention_days": 14,
            "artifact_retention_days": 14,
            "phase": {
                "name": "main",
                "starts_at": "2026-01-01T00:00:00Z",
                "ends_at": "2099-12-31T00:00:00Z",
                "submission_limit_per_day": 5,
                "scoring_version": "v1",
                "rules_version": "v1",
            },
        },
    )
    assert create_response.status_code == 201

    first_scoring_response = client.put(
        "/api/v1/competitions/rescore-code-comp/scoring-config",
        data={
            "metric_name": "code_submission_score",
            "scoring_direction": "max",
            "metric_code": """
from participant_submission import predict

def score_submission():
    rows = [
        {"features": {"value": 2}, "expected": 4},
        {"features": {"value": 5}, "expected": 10},
    ]
    return sum(
        1.0
        for row in rows
        if predict(row["features"]) == row["expected"]
    )
""".strip(),
        },
    )
    assert first_scoring_response.status_code == 200

    from apps.worker.worker import queue as worker_queue

    monkeypatch.setattr(
        worker_queue.process_submission_task,
        "apply_async",
        lambda args: DummyAsyncResult(),
    )

    notebook_payload = json.dumps(
        {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": [
                        "def predict(data):\n",
                        "    return data['value'] * 2\n",
                    ],
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
    ).encode("utf-8")

    submission_response = client.post(
        "/api/v1/competitions/rescore-code-comp/submissions",
        data={"submission_type": "notebook"},
        files={
            "source_file": (
                "submission.ipynb",
                BytesIO(notebook_payload),
                "application/x-ipynb+json",
            )
        },
    )
    assert submission_response.status_code == 202
    process_submission_job(submission_response.json()["id"])

    updated_scoring_response = client.put(
        "/api/v1/competitions/rescore-code-comp/scoring-config",
        data={
            "metric_name": "code_submission_score_v2",
            "scoring_direction": "max",
            "metric_code": """
from participant_submission import predict

def score_submission():
    rows = [
        {"features": {"value": 2}, "expected": 5},
        {"features": {"value": 5}, "expected": 11},
    ]
    return sum(
        1.0
        for row in rows
        if predict(row["features"]) == row["expected"]
    )
""".strip(),
        },
    )
    assert updated_scoring_response.status_code == 200

    rescore_response = client.post("/api/v1/competitions/rescore-code-comp/rescore-submissions")
    assert rescore_response.status_code == 200
    payload = rescore_response.json()
    assert payload["queued_submission_count"] == 1
    assert len(payload["job_ids"]) == 1

    process_submission_job(payload["job_ids"][0])

    submissions_response = client.get("/api/v1/competitions/rescore-code-comp/submissions")
    assert submissions_response.status_code == 200
    submission_payload = submissions_response.json()[0]
    assert submission_payload["latest_score"]["metric_name"] == "code_submission_score_v2"
    assert submission_payload["latest_score"]["public_score_value"] == 0.0
