from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.db.models import LeaderboardEntry, Submission


def upsert_leaderboard_entry(
    db: Session,
    *,
    submission: Submission,
    score_value: float,
    visibility_type: str,
) -> LeaderboardEntry:
    entry = db.scalar(
        select(LeaderboardEntry)
        .where(LeaderboardEntry.competition_id == submission.competition_id)
        .where(LeaderboardEntry.phase_id == submission.phase_id)
        .where(LeaderboardEntry.user_id == submission.user_id)
        .where(LeaderboardEntry.visibility_type == visibility_type)
    )
    if entry is None:
        entry = LeaderboardEntry(
            competition_id=submission.competition_id,
            phase_id=submission.phase_id,
            user_id=submission.user_id,
            best_submission_id=submission.id,
            score_value=score_value,
            visibility_type=visibility_type,
        )
        db.add(entry)
        db.flush()
        return entry

    should_replace = score_value > entry.score_value
    if should_replace:
        entry.score_value = score_value
        entry.best_submission_id = submission.id
    db.flush()
    return entry
