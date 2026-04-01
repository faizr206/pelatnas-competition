from io import BytesIO

from apps.worker.worker.job_handlers.submission_pipeline import process_submission_job


class DummyAsyncResult:
    id = "task-test-123"


def _login_admin(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin1234"},
    )
    assert response.status_code == 200


def test_admin_can_create_competition_and_upload_dataset(client) -> None:
    _login_admin(client)

    competition_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "phase1-comp",
            "title": "Phase 1 Competition",
            "description": "A competition for phase 1",
            "visibility": "public",
            "status": "active",
            "scoring_metric": "row_count",
            "scoring_direction": "max",
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
    assert competition_response.status_code == 201

    dataset_response = client.post(
        "/api/v1/competitions/phase1-comp/datasets",
        data={"name": "starter-dataset"},
        files={"dataset_file": ("dataset.csv", BytesIO(b"id,target\n1,0\n"), "text/csv")},
    )
    assert dataset_response.status_code == 201
    dataset_payload = dataset_response.json()
    assert dataset_payload["version"] == 1
    assert dataset_payload["is_active"] is True

    history_response = client.get("/api/v1/competitions/phase1-comp/datasets")
    assert history_response.status_code == 200
    assert len(history_response.json()) == 1


def test_participant_submission_can_be_processed_and_ranked(client, monkeypatch) -> None:
    _login_admin(client)

    competition_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "ranked-comp",
            "title": "Ranked Competition",
            "description": "A competition for ranked submissions",
            "visibility": "public",
            "status": "active",
            "scoring_metric": "row_count",
            "scoring_direction": "max",
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
    assert competition_response.status_code == 201

    from apps.worker.worker import queue as worker_queue

    monkeypatch.setattr(
        worker_queue.process_submission_task,
        "apply_async",
        lambda args: DummyAsyncResult(),
    )

    submission_response = client.post(
        "/api/v1/competitions/ranked-comp/submissions",
        data={"submission_type": "csv"},
        files={
            "source_file": (
                "submission.csv",
                BytesIO(b"prediction\n0.1\n0.2\n0.3\n"),
                "text/csv",
            )
        },
    )
    assert submission_response.status_code == 202
    job_id = submission_response.json()["id"]

    process_submission_job(job_id)

    submissions_response = client.get("/api/v1/competitions/ranked-comp/submissions")
    assert submissions_response.status_code == 200
    submissions_payload = submissions_response.json()
    assert len(submissions_payload) == 1
    assert submissions_payload[0]["latest_score"]["score_value"] == 3.0

    leaderboard_response = client.get("/api/v1/competitions/ranked-comp/leaderboard")
    assert leaderboard_response.status_code == 200
    leaderboard_payload = leaderboard_response.json()
    assert len(leaderboard_payload) == 1
    assert leaderboard_payload[0]["rank"] == 1
    assert leaderboard_payload[0]["score_value"] == 3.0


def test_submission_job_is_committed_before_worker_can_process_it(client, monkeypatch) -> None:
    _login_admin(client)

    competition_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "commit-safe-comp",
            "title": "Commit Safe Competition",
            "description": "Ensures jobs are committed before enqueue.",
            "visibility": "public",
            "status": "active",
            "scoring_metric": "row_count",
            "scoring_direction": "max",
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
    assert competition_response.status_code == 201

    from apps.worker.worker import queue as worker_queue

    def run_inline(*, args):
        process_submission_job(args[0])
        return DummyAsyncResult()

    monkeypatch.setattr(worker_queue.process_submission_task, "apply_async", run_inline)

    submission_response = client.post(
        "/api/v1/competitions/commit-safe-comp/submissions",
        data={"submission_type": "csv"},
        files={
            "source_file": (
                "submission.csv",
                BytesIO(b"prediction\n0.1\n0.2\n"),
                "text/csv",
            )
        },
    )
    assert submission_response.status_code == 202
    assert submission_response.json()["status"] == "completed"
