from datetime import UTC, datetime
from typing import Any

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


def create_competition(
    db: Session,
    *,
    payload: dict[str, Any],
    created_by: str,
) -> Competition:
    phase_data = payload.pop("phase")
    competition = Competition(created_by=created_by, **payload)
    db.add(competition)
    db.flush()

    phase = CompetitionPhase(competition_id=competition.id, **phase_data)
    db.add(phase)
    db.flush()
    return competition


def update_competition(
    db: Session,
    *,
    competition: Competition,
    payload: dict[str, Any],
) -> Competition:
    phase_data = payload.pop("phase", None)
    for key, value in payload.items():
        setattr(competition, key, value)

    if phase_data is not None:
        phase = get_active_phase(db, competition.id)
        if phase is None:
            phase = CompetitionPhase(competition_id=competition.id, **phase_data)
            db.add(phase)
        else:
            for key, value in phase_data.items():
                setattr(phase, key, value)

    db.flush()
    return competition
