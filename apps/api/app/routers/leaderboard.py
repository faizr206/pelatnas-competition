from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.competitions import get_active_phase, get_competition_by_slug
from apps.api.app.schemas.leaderboard import LeaderboardEntryResponse
from packages.db.models import LeaderboardEntry, Submission, User

router = APIRouter(prefix="/competitions/{slug}/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[LeaderboardEntryResponse])
def leaderboard(slug: str, db: Session = Depends(get_db)) -> list[LeaderboardEntryResponse]:
    return _read_leaderboard(db=db, slug=slug, visibility_type="public")


@router.get("/public", response_model=list[LeaderboardEntryResponse])
def public_leaderboard(slug: str, db: Session = Depends(get_db)) -> list[LeaderboardEntryResponse]:
    return _read_leaderboard(db=db, slug=slug, visibility_type="public")


@router.get("/private", response_model=list[LeaderboardEntryResponse])
def private_leaderboard(slug: str, db: Session = Depends(get_db)) -> list[LeaderboardEntryResponse]:
    return _read_leaderboard(db=db, slug=slug, visibility_type="private")


def _read_leaderboard(
    *, db: Session, slug: str, visibility_type: str
) -> list[LeaderboardEntryResponse]:
    competition = get_competition_by_slug(db, slug=slug)
    if competition is None:
        raise HTTPException(status_code=404, detail="Competition not found.")

    phase = get_active_phase(db, competition_id=competition.id)
    if phase is None:
        return []

    rows = db.execute(
        select(LeaderboardEntry, Submission, User)
        .join(Submission, Submission.id == LeaderboardEntry.best_submission_id)
        .join(User, User.id == LeaderboardEntry.user_id)
        .where(LeaderboardEntry.competition_id == competition.id)
        .where(LeaderboardEntry.phase_id == phase.id)
        .where(LeaderboardEntry.visibility_type == visibility_type)
        .order_by(LeaderboardEntry.rank.asc(), Submission.created_at.asc())
    ).all()

    return [
        LeaderboardEntryResponse(
            rank=entry.rank,
            score_value=entry.score_value,
            user_id=entry.user_id,
            best_submission_id=entry.best_submission_id,
            submission_created_at=submission.created_at,
            submitter_email=user.email,
            submitter_name=user.display_name,
        )
        for entry, submission, user in rows
    ]
