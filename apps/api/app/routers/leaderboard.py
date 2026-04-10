from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.dependencies.auth import get_optional_current_user
from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.competitions import get_active_phase, get_competition_by_slug
from apps.api.app.schemas.leaderboard import LeaderboardEntryResponse
from packages.core.time import utcnow
from packages.db.models import LeaderboardEntry, Submission, User

router = APIRouter(prefix="/competitions/{slug}/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[LeaderboardEntryResponse])
def leaderboard(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> list[LeaderboardEntryResponse]:
    return _read_leaderboard(
        db=db,
        slug=slug,
        visibility_type="public",
        current_user=current_user,
    )


@router.get("/public", response_model=list[LeaderboardEntryResponse])
def public_leaderboard(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> list[LeaderboardEntryResponse]:
    return _read_leaderboard(
        db=db,
        slug=slug,
        visibility_type="public",
        current_user=current_user,
    )


@router.get("/private", response_model=list[LeaderboardEntryResponse])
def private_leaderboard(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> list[LeaderboardEntryResponse]:
    return _read_leaderboard(
        db=db,
        slug=slug,
        visibility_type="private",
        current_user=current_user,
    )


def _read_leaderboard(
    *,
    db: Session,
    slug: str,
    visibility_type: str,
    current_user: User | None = None,
) -> list[LeaderboardEntryResponse]:
    competition = get_competition_by_slug(db, slug=slug, current_user=current_user)
    if competition is None:
        raise HTTPException(status_code=404, detail="Competition not found.")

    phase = get_active_phase(db, competition_id=competition.id)
    if phase is None:
        return []
    now = utcnow()
    phase_starts_at = _as_utc(phase.starts_at)
    if phase_starts_at > now:
        return []
    if (
        visibility_type == "private"
        and not _private_scores_visible_at(
            competition=competition,
            phase=phase,
            now=now,
        )
        and not (current_user and current_user.is_admin)
    ):
        raise HTTPException(
            status_code=404,
            detail="Private leaderboard is unavailable until the configured unlock time.",
        )

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


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _private_scores_visible_at(*, competition, phase, now: datetime) -> bool:
    opens_at = competition.private_leaderboard_opens_at or phase.ends_at
    return _as_utc(opens_at) < now
