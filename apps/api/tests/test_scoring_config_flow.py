from io import BytesIO
import json

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
                "ends_at": "2026-12-31T00:00:00Z",
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
                BytesIO(b"Id,target\n1,1.0\n2,2.0\n"),
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
    assert submission_payload["latest_score"]["score_value"] == 0.625


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

    artifacts_response = client.get(
        f"/api/v1/submissions/{submission_payload['id']}/artifacts"
    )
    assert artifacts_response.status_code == 200
    artifact_types = {item["artifact_type"] for item in artifacts_response.json()}
    assert "participant_submission.py" in artifact_types
