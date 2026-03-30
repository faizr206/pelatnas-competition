from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from apps.api.app.config import get_settings
from apps.worker.worker.job_handlers.submission_pipeline import process_submission_job
from packages.auth.security import hash_password
from packages.core.constants import JobStatus
from packages.db.base import Base
from packages.db.models import Competition, CompetitionPhase, Job, Score, Submission, User
from packages.db.session import get_engine, session_scope


def test_process_submission_job_updates_job_and_submission(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'worker.db'}")
    monkeypatch.setenv("LOCAL_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("WORKER_ID", "worker-test")
    get_settings.cache_clear()
    get_engine.cache_clear()

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    source_path = tmp_path / "submission.csv"
    source_path.write_text("prediction\n1\n2\n3\n", encoding="utf-8")

    now = datetime.now(UTC)
    with session_scope() as session:
        user = User(
            email="worker@example.com",
            display_name="Worker Test",
            password_hash=hash_password("password"),
            status="active",
            is_admin=True,
        )
        session.add(user)
        session.flush()

        competition = Competition(
            slug="worker-comp",
            title="Worker Competition",
            description="Worker test competition",
            visibility="public",
            status="active",
            created_by=user.id,
            scoring_metric="row_count",
            scoring_direction="max",
            best_submission_rule="best_score",
            max_submissions_per_day=5,
            max_runtime_minutes=20,
            max_memory_mb=4096,
            max_cpu=2,
            allow_csv_submissions=True,
            allow_notebook_submissions=True,
            source_retention_days=30,
            log_retention_days=14,
            artifact_retention_days=14,
        )
        session.add(competition)
        session.flush()

        phase = CompetitionPhase(
            competition_id=competition.id,
            name="phase-1-file-submission",
            starts_at=now - timedelta(days=1),
            ends_at=now + timedelta(days=1),
            submission_limit_per_day=5,
            scoring_version="v1",
            rules_version="v1",
        )
        session.add(phase)
        session.flush()

        submission = Submission(
            competition_id=competition.id,
            phase_id=phase.id,
            user_id=user.id,
            submission_type="csv",
            source_archive_path=str(source_path),
            manifest_path=None,
            source_original_filename="submission.csv",
            source_content_type="text/csv",
            source_checksum="checksum",
            source_size_bytes=source_path.stat().st_size,
            status="queued",
        )
        session.add(submission)
        session.flush()

        job = Job(
            submission_id=submission.id,
            job_type="submission_pipeline",
            status=JobStatus.QUEUED.value,
            queued_at=now,
        )
        session.add(job)
        session.flush()
        job_id = job.id
        submission_id = submission.id

    processed_job_id = process_submission_job(job_id)
    assert processed_job_id == job_id

    with session_scope() as session:
        job = session.get(Job, job_id)
        submission = session.get(Submission, submission_id)
        score = session.scalar(select(Score).where(Score.submission_id == submission_id))
        assert job is not None
        assert submission is not None
        assert score is not None
        assert job.status == JobStatus.COMPLETED.value
        assert submission.status == "completed"
        assert score.metric_name == "row_count"
        assert score.score_value == 3.0
        assert Path(tmp_path / "storage" / "artifacts" / submission_id / "stdout.log").exists()
