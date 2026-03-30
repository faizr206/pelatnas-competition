from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.db.models import Competition, CompetitionPhase


def list_competitions(db: Session) -> list[Competition]:
    return list(db.scalars(select(Competition).order_by(Competition.created_at.desc())).all())


def get_competition_by_slug(db: Session, slug: str) -> Competition | None:
    return db.scalar(select(Competition).where(Competition.slug == slug))


def get_active_phase(db: Session, competition_id: str) -> CompetitionPhase | None:
    now = datetime.now(UTC)
    phase = db.scalar(
        select(CompetitionPhase)
        .where(CompetitionPhase.competition_id == competition_id)
        .where(CompetitionPhase.starts_at <= now)
        .where(CompetitionPhase.ends_at >= now)
        .order_by(CompetitionPhase.starts_at.asc())
    )
    if phase is not None:
        return phase

    return db.scalar(
        select(CompetitionPhase)
        .where(CompetitionPhase.competition_id == competition_id)
        .order_by(CompetitionPhase.starts_at.asc())
    )
