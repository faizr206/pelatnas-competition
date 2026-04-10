from datetime import UTC, datetime
from io import BytesIO

from sqlalchemy import select

from apps.api.app.config import get_settings
from apps.worker.worker.job_handlers.submission_pipeline import process_submission_job
from packages.db.models import Competition, CompetitionPhase
from packages.db.session import session_scope


class DummyAsyncResult:
    id = "task-test-123"


def _login_admin(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin1234"},
    )
    assert response.status_code == 200


def _create_user_and_login(client, *, email: str, password: str, display_name: str) -> None:
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin1234"},
    )
    assert admin_login.status_code == 200
    create_response = client.post(
        "/api/v1/admin/users",
        json={
            "email": email,
            "display_name": display_name,
            "default_password": password,
            "is_admin": False,
            "status": "active",
        },
    )
    assert create_response.status_code == 201
    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204
    user_login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert user_login.status_code == 200


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


def test_upcoming_competition_is_hidden_from_public_until_phase_start(client) -> None:
    _login_admin(client)

    competition_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "future-comp",
            "title": "Future Competition",
            "description": "Hidden before the phase starts",
            "visibility": "public",
            "status": "active",
            "scoring_metric": "row_count",
            "scoring_direction": "max",
            "phase": {
                "name": "main",
                "starts_at": "2099-01-01T00:00:00Z",
                "ends_at": "2099-12-31T00:00:00Z",
                "submission_limit_per_day": 5,
                "scoring_version": "v1",
                "rules_version": "v1",
            },
        },
    )
    assert competition_response.status_code == 201

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204

    public_list_response = client.get("/api/v1/competitions")
    assert public_list_response.status_code == 200
    assert all(item["slug"] != "future-comp" for item in public_list_response.json())

    public_detail_response = client.get("/api/v1/competitions/future-comp")
    assert public_detail_response.status_code == 404

    _create_user_and_login(
        client,
        email="participant-future@example.com",
        password="participant1234",
        display_name="Future Participant",
    )

    participant_list_response = client.get("/api/v1/competitions")
    assert participant_list_response.status_code == 200
    assert all(item["slug"] != "future-comp" for item in participant_list_response.json())

    participant_detail_response = client.get("/api/v1/competitions/future-comp")
    assert participant_detail_response.status_code == 404


def test_admin_can_access_upcoming_competition_detail_before_start(client) -> None:
    _login_admin(client)

    competition_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "future-admin-access-comp",
            "title": "Future Admin Access Competition",
            "description": "Admins can access this before start",
            "visibility": "public",
            "status": "active",
            "scoring_metric": "row_count",
            "scoring_direction": "max",
            "phase": {
                "name": "main",
                "starts_at": "2099-01-01T00:00:00Z",
                "ends_at": "2099-12-31T00:00:00Z",
                "submission_limit_per_day": 5,
                "scoring_version": "v1",
                "rules_version": "v1",
            },
        },
    )
    assert competition_response.status_code == 201

    detail_response = client.get("/api/v1/competitions/future-admin-access-comp")
    assert detail_response.status_code == 200
    assert detail_response.json()["slug"] == "future-admin-access-comp"

    leaderboard_response = client.get("/api/v1/competitions/future-admin-access-comp/leaderboard")
    assert leaderboard_response.status_code == 200


def test_dataset_upload_rejects_disallowed_extension(client) -> None:
    _login_admin(client)

    competition_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "dataset-guard-comp",
            "title": "Dataset Guard Competition",
            "description": "Dataset validation test",
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
        "/api/v1/competitions/dataset-guard-comp/datasets",
        data={"name": "bad-dataset"},
        files={
            "dataset_file": ("dataset.exe", BytesIO(b"not allowed"), "application/octet-stream")
        },
    )
    assert dataset_response.status_code == 400


def test_submission_upload_rejects_oversized_payload(client, monkeypatch) -> None:
    monkeypatch.setenv("MAX_SUBMISSION_UPLOAD_BYTES", "8")
    get_settings.cache_clear()
    _login_admin(client)

    competition_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "submission-size-comp",
            "title": "Submission Size Competition",
            "description": "Submission size validation test",
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

    submission_response = client.post(
        "/api/v1/competitions/submission-size-comp/submissions",
        data={"submission_type": "csv"},
        files={
            "source_file": (
                "submission.csv",
                BytesIO(b"prediction\n0.1\n"),
                "text/csv",
            )
        },
    )
    assert submission_response.status_code == 413


def test_notebook_submission_rejects_wrong_extension(client, monkeypatch) -> None:
    _login_admin(client)

    competition_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "notebook-guard-comp",
            "title": "Notebook Guard Competition",
            "description": "Notebook validation test",
            "visibility": "public",
            "status": "active",
            "submission_mode": "code_submission",
            "allow_csv_submissions": False,
            "allow_notebook_submissions": True,
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
        "/api/v1/competitions/notebook-guard-comp/submissions",
        data={"submission_type": "notebook"},
        files={
            "source_file": (
                "analysis.py",
                BytesIO(b"print('hello')"),
                "application/json",
            )
        },
    )
    assert submission_response.status_code == 400


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


def test_private_leaderboard_unlocks_after_phase_end_and_late_submissions_do_not_count(
    client, monkeypatch
) -> None:
    _login_admin(client)

    competition_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "freeze-comp",
            "title": "Freeze Competition",
            "description": "Leaderboard freeze and late submissions",
            "visibility": "public",
            "status": "active",
            "scoring_metric": "row_count",
            "scoring_direction": "max",
            "phase": {
                "name": "main",
                "starts_at": "2020-01-01T00:00:00Z",
                "ends_at": "2099-12-31T00:00:00Z",
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

    first_submission_response = client.post(
        "/api/v1/competitions/freeze-comp/submissions",
        data={"submission_type": "csv"},
        files={
            "source_file": (
                "submission.csv",
                BytesIO(b"prediction\n0.1\n0.2\n0.3\n"),
                "text/csv",
            )
        },
    )
    assert first_submission_response.status_code == 202
    process_submission_job(first_submission_response.json()["id"])

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204
    private_before_end = client.get("/api/v1/competitions/freeze-comp/leaderboard/private")
    assert private_before_end.status_code == 404

    _login_admin(client)

    with session_scope() as session:
        competition = session.scalar(select(Competition).where(Competition.slug == "freeze-comp"))
        assert competition is not None
        phase = session.scalar(
            select(CompetitionPhase).where(CompetitionPhase.competition_id == competition.id)
        )
        assert phase is not None
        phase.ends_at = datetime(2020, 1, 2, tzinfo=UTC)
        session.flush()

    late_submission_response = client.post(
        "/api/v1/competitions/freeze-comp/submissions",
        data={"submission_type": "csv"},
        files={
            "source_file": (
                "late-submission.csv",
                BytesIO(b"prediction\n0.1\n0.2\n0.3\n0.4\n0.5\n"),
                "text/csv",
            )
        },
    )
    assert late_submission_response.status_code == 202
    process_submission_job(late_submission_response.json()["id"])

    submissions_response = client.get("/api/v1/competitions/freeze-comp/submissions")
    assert submissions_response.status_code == 200
    submissions_payload = submissions_response.json()
    assert submissions_payload[0]["is_late_submission"] is True
    assert submissions_payload[0]["latest_score"]["score_value"] == 5.0
    assert submissions_payload[1]["is_late_submission"] is False

    public_leaderboard_response = client.get("/api/v1/competitions/freeze-comp/leaderboard/public")
    assert public_leaderboard_response.status_code == 200
    public_leaderboard_payload = public_leaderboard_response.json()
    assert len(public_leaderboard_payload) == 1
    assert public_leaderboard_payload[0]["score_value"] == 3.0

    private_leaderboard_response = client.get(
        "/api/v1/competitions/freeze-comp/leaderboard/private"
    )
    assert private_leaderboard_response.status_code == 200
    private_leaderboard_payload = private_leaderboard_response.json()
    assert len(private_leaderboard_payload) == 1
    assert private_leaderboard_payload[0]["score_value"] == 3.0


def test_admin_can_view_private_leaderboard_before_unlock(client, monkeypatch) -> None:
    _login_admin(client)

    competition_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "admin-private-comp",
            "title": "Admin Private Competition",
            "description": "Admins can inspect private standings early",
            "visibility": "public",
            "status": "active",
            "scoring_metric": "row_count",
            "scoring_direction": "max",
            "private_leaderboard_opens_at": "2099-01-15T00:00:00Z",
            "phase": {
                "name": "main",
                "starts_at": "2020-01-01T00:00:00Z",
                "ends_at": "2099-12-31T00:00:00Z",
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
        "/api/v1/competitions/admin-private-comp/submissions",
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
    process_submission_job(submission_response.json()["id"])

    private_leaderboard_response = client.get(
        "/api/v1/competitions/admin-private-comp/leaderboard/private"
    )
    assert private_leaderboard_response.status_code == 200
    private_leaderboard_payload = private_leaderboard_response.json()
    assert len(private_leaderboard_payload) == 1
    assert private_leaderboard_payload[0]["score_value"] == 3.0


def test_private_leaderboard_unlock_can_be_set_independently_of_phase_end(
    client, monkeypatch
) -> None:
    _login_admin(client)

    competition_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "manual-unlock-comp",
            "title": "Manual Unlock Competition",
            "description": "Private leaderboard unlock time is configurable",
            "visibility": "public",
            "status": "active",
            "scoring_metric": "mse",
            "scoring_direction": "min",
            "submission_mode": "prediction_file",
            "private_leaderboard_opens_at": "2099-01-15T00:00:00Z",
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
    assert competition_response.status_code == 201

    scoring_response = client.put(
        "/api/v1/competitions/manual-unlock-comp/scoring-config",
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
                BytesIO(b"Id,target,Usage\n1,1.0,Public\n2,2.0,Private\n"),
                "text/csv",
            )
        },
    )
    assert scoring_response.status_code == 200

    from apps.worker.worker import queue as worker_queue

    monkeypatch.setattr(
        worker_queue.process_submission_task,
        "apply_async",
        lambda args: DummyAsyncResult(),
    )

    submission_response = client.post(
        "/api/v1/competitions/manual-unlock-comp/submissions",
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

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204
    private_before_unlock = client.get(
        "/api/v1/competitions/manual-unlock-comp/leaderboard/private"
    )
    assert private_before_unlock.status_code == 404

    _login_admin(client)

    with session_scope() as session:
        competition = session.scalar(
            select(Competition).where(Competition.slug == "manual-unlock-comp")
        )
        assert competition is not None
        competition.private_leaderboard_opens_at = datetime(2020, 1, 2, tzinfo=UTC)
        session.flush()

    submissions_response = client.get("/api/v1/competitions/manual-unlock-comp/submissions")
    assert submissions_response.status_code == 200
    submission_payload = submissions_response.json()[0]
    assert submission_payload["latest_score"]["public_score_value"] == 0.25
    assert submission_payload["latest_score"]["private_score_value"] == 1.0
    assert submission_payload["latest_score"]["score_value"] == 1.0

    private_after_unlock = client.get("/api/v1/competitions/manual-unlock-comp/leaderboard/private")
    assert private_after_unlock.status_code == 200
    assert private_after_unlock.json()[0]["score_value"] == 1.0


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


def test_hidden_admin_submissions_are_excluded_from_leaderboard(client, monkeypatch) -> None:
    _login_admin(client)

    competition_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "hidden-admin-comp",
            "title": "Hidden Admin Competition",
            "description": "Admin can hide own submissions from leaderboard",
            "visibility": "public",
            "status": "active",
            "scoring_metric": "row_count",
            "scoring_direction": "max",
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
    assert competition_response.status_code == 201

    from apps.worker.worker import queue as worker_queue

    monkeypatch.setattr(
        worker_queue.process_submission_task,
        "apply_async",
        lambda args: DummyAsyncResult(),
    )

    submission_response = client.post(
        "/api/v1/competitions/hidden-admin-comp/submissions",
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
    process_submission_job(submission_response.json()["id"])

    visible_leaderboard_response = client.get(
        "/api/v1/competitions/hidden-admin-comp/leaderboard/public"
    )
    assert visible_leaderboard_response.status_code == 200
    assert len(visible_leaderboard_response.json()) == 1

    hide_response = client.patch(
        "/api/v1/auth/me/leaderboard-visibility",
        json={"hide_from_leaderboard": True},
    )
    assert hide_response.status_code == 200

    leaderboard_response = client.get("/api/v1/competitions/hidden-admin-comp/leaderboard/public")
    assert leaderboard_response.status_code == 200
    assert leaderboard_response.json() == []


def test_admin_can_hide_individual_submission_from_leaderboard(client, monkeypatch) -> None:
    _login_admin(client)

    competition_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "submission-visibility-comp",
            "title": "Submission Visibility Competition",
            "description": "Admins can hide individual submissions from leaderboard",
            "visibility": "public",
            "status": "active",
            "scoring_metric": "row_count",
            "scoring_direction": "max",
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
    assert competition_response.status_code == 201

    from apps.worker.worker import queue as worker_queue

    monkeypatch.setattr(
        worker_queue.process_submission_task,
        "apply_async",
        lambda args: DummyAsyncResult(),
    )

    submission_response = client.post(
        "/api/v1/competitions/submission-visibility-comp/submissions",
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
    process_submission_job(submission_response.json()["id"])

    submissions_response = client.get("/api/v1/competitions/submission-visibility-comp/submissions")
    assert submissions_response.status_code == 200
    submission_payload = submissions_response.json()[0]
    assert submission_payload["display_on_leaderboard"] is True

    leaderboard_before = client.get(
        "/api/v1/competitions/submission-visibility-comp/leaderboard/public"
    )
    assert leaderboard_before.status_code == 200
    assert len(leaderboard_before.json()) == 1

    hide_response = client.patch(
        f"/api/v1/submissions/{submission_payload['id']}/leaderboard-visibility",
        json={"display_on_leaderboard": False},
    )
    assert hide_response.status_code == 200
    assert hide_response.json()["display_on_leaderboard"] is False

    leaderboard_after = client.get(
        "/api/v1/competitions/submission-visibility-comp/leaderboard/public"
    )
    assert leaderboard_after.status_code == 200
    assert leaderboard_after.json() == []
