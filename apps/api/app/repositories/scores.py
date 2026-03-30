from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.db.models import Score


def get_latest_score_for_submission(db: Session, *, submission_id: str) -> Score | None:
    return db.scalar(
        select(Score).where(Score.submission_id == submission_id).order_by(Score.created_at.desc())
    )
