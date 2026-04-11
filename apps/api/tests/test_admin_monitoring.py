from sqlalchemy import select

from packages.auth.security import hash_password
from packages.core.time import utcnow
from packages.db.models import (
    Competition,
    CompetitionPhase,
    Job,
    LeaderboardEntry,
    Score,
    Submission,
    User,
    WorkerNode,
)
from packages.leaderboard.service import refresh_leaderboard
from packages.db.session import session_scope
from packages.storage.service import get_object, save_text_file


def _login_admin(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin1234"},
    )
    assert response.status_code == 200


def test_admin_can_view_workers_and_tasks(client) -> None:
    _login_admin(client)

    me_response = client.get("/api/v1/auth/me")
    admin_id = me_response.json()["id"]

    with session_scope() as session:
        participant = User(
            email="participant@example.com",
            display_name="Participant One",
            password_hash=hash_password("participant-pass-123"),
            status="active",
            is_admin=False,
        )
        session.add(participant)
        session.flush()

        competition = session.scalar(select(Competition).where(Competition.slug == "test-comp"))
        if competition is None:
            raise AssertionError("Expected bootstrap competition to exist.")

        phase = session.scalar(
            select(CompetitionPhase).where(CompetitionPhase.competition_id == competition.id)
        )
        if phase is None:
            raise AssertionError("Expected bootstrap phase to exist.")

        submission = Submission(
            competition_id=competition.id,
            phase_id=phase.id,
            user_id=participant.id,
            submission_type="csv",
            source_archive_path="/app/data/storage/submissions/test.csv",
            manifest_path=None,
            source_original_filename="submission.csv",
            source_content_type="text/csv",
            source_checksum="abc123",
            source_size_bytes=128,
            status="completed",
        )
        session.add(submission)
        session.flush()

        session.add(
            Job(
                submission_id=submission.id,
                job_type="submission_pipeline",
                status="completed",
                worker_id="worker-remote-1",
                retry_count=0,
                failure_reason=None,
            )
        )
        session.add(
            Score(
                submission_id=submission.id,
                metric_name="row_count",
                metric_value=42.0,
                score_value=42.0,
                public_score_value=42.0,
                private_score_value=42.0,
                scoring_version="v1",
            )
        )

        failed_submission = Submission(
            competition_id=competition.id,
            phase_id=phase.id,
            user_id=admin_id,
            submission_type="notebook",
            source_archive_path="/app/data/storage/submissions/test.ipynb",
            manifest_path=None,
            source_original_filename="analysis.ipynb",
            source_content_type="application/x-ipynb+json",
            source_checksum="def456",
            source_size_bytes=512,
            status="failed",
        )
        session.add(failed_submission)
        session.flush()

        session.add(
            Job(
                submission_id=failed_submission.id,
                job_type="submission_pipeline",
                status="failed",
                worker_id="worker-remote-2",
                retry_count=1,
                failure_reason="Notebook validation failed.",
            )
        )
        session.add(
            WorkerNode(
                worker_id="worker-remote-1",
                is_enabled=True,
                gpu_available=True,
                last_heartbeat_at=utcnow(),
            )
        )
        session.add(
            WorkerNode(
                worker_id="worker-remote-2",
                is_enabled=False,
                gpu_available=False,
                last_heartbeat_at=utcnow(),
            )
        )

    workers_response = client.get("/api/v1/admin/workers")
    assert workers_response.status_code == 200
    workers = workers_response.json()
    assert [worker["worker_id"] for worker in workers] == ["worker-remote-1", "worker-remote-2"]
    assert workers[0]["completed_jobs"] == 1
    assert workers[0]["availability_status"] == "idle"
    assert workers[0]["is_online"] is True
    assert workers[0]["is_enabled"] is True
    assert workers[0]["gpu_available"] is True
    assert workers[1]["failed_jobs"] == 1
    assert workers[1]["availability_status"] == "disabled"
    assert workers[1]["is_enabled"] is False
    assert workers[1]["gpu_available"] is False

    tasks_response = client.get("/api/v1/admin/tasks")
    assert tasks_response.status_code == 200
    tasks = tasks_response.json()
    assert len(tasks) == 2
    assert tasks[0]["latest_job"]["worker_id"] == "worker-remote-2"
    assert tasks[0]["latest_job"]["status"] == "failed"
    assert tasks[1]["participant_email"] == "participant@example.com"
    assert tasks[1]["latest_score"]["score_value"] == 42.0
    assert tasks[1]["source_size_bytes"] == 128


def test_admin_can_list_competition_submissions_and_download_source_file(client) -> None:
    _login_admin(client)

    with session_scope() as session:
        competition = session.scalar(select(Competition).where(Competition.slug == "test-comp"))
        if competition is None:
            raise AssertionError("Expected bootstrap competition to exist.")
        competition_id = competition.id

        phase = session.scalar(
            select(CompetitionPhase).where(CompetitionPhase.competition_id == competition.id)
        )
        if phase is None:
            raise AssertionError("Expected bootstrap phase to exist.")

        participant = User(
            email="viewer@example.com",
            display_name="Viewer Participant",
            password_hash=hash_password("viewer-pass-123"),
            status="active",
            is_admin=False,
        )
        session.add(participant)
        session.flush()

        source_key = save_text_file(
            "",
            category="submissions",
            competition_slug=competition.slug,
            filename="source.csv",
            contents="prediction\n0.1\n",
        )
        submission = Submission(
            competition_id=competition.id,
            phase_id=phase.id,
            user_id=participant.id,
            submission_type="csv",
            source_archive_path=source_key,
            manifest_path=None,
            source_original_filename="source.csv",
            source_content_type="text/csv",
            source_checksum="checksum-1",
            source_size_bytes=15,
            status="completed",
        )
        session.add(submission)
        session.flush()
        submission_id = submission.id

    list_response = client.get("/api/v1/admin/competitions/test-comp/submissions")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert len(payload) == 1
    assert payload[0]["source_original_filename"] == "source.csv"
    assert payload[0]["participant_email"] == "viewer@example.com"
    assert payload[0]["source_size_bytes"] == 15

    download_response = client.get(f"/api/v1/admin/submissions/{submission_id}/source-file")
    assert download_response.status_code == 200
    assert download_response.text == "prediction\n0.1\n"


def test_admin_can_delete_any_participant_submission_from_competition(client) -> None:
    _login_admin(client)

    with session_scope() as session:
        competition = session.scalar(select(Competition).where(Competition.slug == "test-comp"))
        if competition is None:
            raise AssertionError("Expected bootstrap competition to exist.")
        competition_id = competition.id

        phase = session.scalar(
            select(CompetitionPhase).where(CompetitionPhase.competition_id == competition.id)
        )
        if phase is None:
            raise AssertionError("Expected bootstrap phase to exist.")

        participant = User(
            email="delete-me@example.com",
            display_name="Delete Me",
            password_hash=hash_password("delete-pass-123"),
            status="active",
            is_admin=False,
        )
        session.add(participant)
        session.flush()

        source_key = save_text_file(
            "",
            category="submissions",
            competition_slug=competition.slug,
            filename="delete-source.csv",
            contents="prediction\n0.9\n",
        )
        submission = Submission(
            competition_id=competition.id,
            phase_id=phase.id,
            user_id=participant.id,
            submission_type="csv",
            source_archive_path=source_key,
            manifest_path=None,
            source_original_filename="delete-source.csv",
            source_content_type="text/csv",
            source_checksum="checksum-delete",
            source_size_bytes=15,
            status="completed",
            display_on_leaderboard=True,
        )
        session.add(submission)
        session.flush()

        session.add(
            Score(
                submission_id=submission.id,
                metric_name="row_count",
                metric_value=7.0,
                score_value=7.0,
                public_score_value=7.0,
                private_score_value=7.0,
                scoring_version="v1",
            )
        )
        refresh_leaderboard(
            session,
            competition=competition,
            phase_id=phase.id,
            visibility_type="public",
        )
        refresh_leaderboard(
            session,
            competition=competition,
            phase_id=phase.id,
            visibility_type="private",
        )
        session.commit()
        submission_id = submission.id

    list_response = client.get("/api/v1/admin/competitions/test-comp/submissions")
    assert list_response.status_code == 200
    assert any(
        item["submission_id"] == submission_id for item in list_response.json()
    )

    delete_response = client.delete(
        f"/api/v1/admin/competitions/test-comp/submissions/{submission_id}"
    )
    assert delete_response.status_code == 204

    with session_scope() as session:
        assert session.get(Submission, submission_id) is None
        remaining_entries = list(
            session.scalars(
                select(LeaderboardEntry).where(LeaderboardEntry.competition_id == competition_id)
            ).all()
        )
        assert remaining_entries == []

    try:
        get_object(source_key)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected deleted submission source file to be removed from storage.")


def test_admin_can_view_upcoming_competitions_from_admin_endpoints(client) -> None:
    _login_admin(client)

    create_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "future-admin-comp",
            "title": "Future Admin Competition",
            "description": "Only admins should see this before it starts",
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
    assert create_response.status_code == 201

    list_response = client.get("/api/v1/admin/competitions")
    assert list_response.status_code == 200
    assert any(item["slug"] == "future-admin-comp" for item in list_response.json())

    detail_response = client.get("/api/v1/admin/competitions/future-admin-comp")
    assert detail_response.status_code == 200
    assert detail_response.json()["slug"] == "future-admin-comp"


def test_admin_can_enable_and_disable_worker(client) -> None:
    _login_admin(client)

    with session_scope() as session:
        session.add(
            WorkerNode(
                worker_id="worker-toggle-1",
                is_enabled=True,
                gpu_available=False,
                last_heartbeat_at=utcnow(),
            )
        )

    disable_response = client.patch(
        "/api/v1/admin/workers/worker-toggle-1",
        json={"is_enabled": False},
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["is_enabled"] is False
    assert disable_response.json()["availability_status"] == "disabled"

    enable_response = client.patch(
        "/api/v1/admin/workers/worker-toggle-1",
        json={"is_enabled": True},
    )
    assert enable_response.status_code == 200
    assert enable_response.json()["is_enabled"] is True
