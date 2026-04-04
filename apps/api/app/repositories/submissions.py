from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from packages.db.models import Submission


def create_submission(
    db: Session,
    *,
    competition_id: str,
    phase_id: str,
    user_id: str,
    submission_type: str,
    source_archive_path: str,
    manifest_path: str | None,
    source_original_filename: str,
    source_content_type: str,
    source_checksum: str,
    source_size_bytes: int,
    is_late_submission: bool,
) -> Submission:
    submission = Submission(
        competition_id=competition_id,
        phase_id=phase_id,
        user_id=user_id,
        submission_type=submission_type,
        source_archive_path=source_archive_path,
        manifest_path=manifest_path,
        source_original_filename=source_original_filename,
        source_content_type=source_content_type,
        source_checksum=source_checksum,
        source_size_bytes=source_size_bytes,
        is_late_submission=is_late_submission,
        status="pending",
    )
    db.add(submission)
    db.flush()
    return submission


def list_submissions_for_user(
    db: Session, *, competition_id: str, user_id: str
) -> list[Submission]:
    return list(
        db.scalars(
            select(Submission)
            .where(Submission.competition_id == competition_id)
            .where(Submission.user_id == user_id)
            .order_by(Submission.created_at.desc())
        ).all()
    )


def get_submission_by_id(db: Session, submission_id: str) -> Submission | None:
    return db.scalar(select(Submission).where(Submission.id == submission_id))


def count_submissions_for_day(
    db: Session,
    *,
    competition_id: str,
    user_id: str,
    when: datetime | None = None,
) -> int:
    current = when or datetime.now(UTC)
    start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return int(
        db.scalar(
            select(func.count(Submission.id))
            .where(Submission.competition_id == competition_id)
            .where(Submission.user_id == user_id)
            .where(Submission.created_at >= start)
            .where(Submission.created_at < end)
        )
        or 0
    )
