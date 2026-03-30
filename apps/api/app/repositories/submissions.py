from sqlalchemy import select
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
    manifest_path: str,
) -> Submission:
    submission = Submission(
        competition_id=competition_id,
        phase_id=phase_id,
        user_id=user_id,
        submission_type=submission_type,
        source_archive_path=source_archive_path,
        manifest_path=manifest_path,
        status="queued",
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
