from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from apps.api.app.config import Settings
from packages.auth.security import hash_password
from packages.db.models import Competition, CompetitionPhase, User
from packages.db.session import session_scope
from packages.storage.service import ensure_storage_root


def bootstrap_local_state(settings: Settings) -> None:
    ensure_storage_root(settings.local_storage_root)

    with session_scope() as session:
        user = session.scalar(
            select(User).where(User.email == settings.default_admin_email.lower())
        )
        if user is None:
            user = User(
                email=settings.default_admin_email.lower(),
                display_name=settings.default_admin_name,
                password_hash=hash_password(settings.default_admin_password),
                status="active",
                is_admin=True,
            )
            session.add(user)
            session.flush()

        competition = session.scalar(
            select(Competition).where(Competition.slug == settings.default_competition_slug)
        )
        if competition is None:
            competition = Competition(
                slug=settings.default_competition_slug,
                title=settings.default_competition_title,
                description=settings.default_competition_description,
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

        phase = session.scalar(
            select(CompetitionPhase).where(CompetitionPhase.competition_id == competition.id)
        )
        if phase is None:
            now = datetime.now(UTC)
            session.add(
                CompetitionPhase(
                    competition_id=competition.id,
                    name="phase-1-file-submission",
                    starts_at=now - timedelta(days=1),
                    ends_at=now + timedelta(days=30),
                    submission_limit_per_day=5,
                    scoring_version="v1",
                    rules_version="v1",
                )
            )
