from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from packages.core.time import utcnow
from packages.db.models import Competition, Submission, SubmissionArtifact
from packages.db.session import session_scope
from packages.observability.logging import get_logger
from packages.storage.service import delete_file_if_present

logger = get_logger(__name__)


def cleanup_retention_targets() -> int:
    deleted_files = 0
    now = utcnow()

    with session_scope() as session:
        competitions = list(session.scalars(select(Competition)).all())
        for competition in competitions:
            source_deadline = now - timedelta(days=competition.source_retention_days)
            log_deadline = now - timedelta(days=competition.log_retention_days)
            artifact_deadline = now - timedelta(days=competition.artifact_retention_days)

            source_submissions = list(
                session.scalars(
                    select(Submission)
                    .where(Submission.competition_id == competition.id)
                    .where(Submission.created_at < source_deadline)
                    .where(Submission.status != "completed")
                ).all()
            )
            for submission in source_submissions:
                delete_file_if_present(submission.source_archive_path)
                deleted_files += 1

            artifacts = list(
                session.scalars(
                    select(SubmissionArtifact)
                    .join(Submission, Submission.id == SubmissionArtifact.submission_id)
                    .where(Submission.competition_id == competition.id)
                    .where(
                        (
                            (SubmissionArtifact.artifact_type == "stdout.log")
                            & (SubmissionArtifact.created_at < log_deadline)
                        )
                        | (
                            (SubmissionArtifact.artifact_type != "stdout.log")
                            & (SubmissionArtifact.created_at < artifact_deadline)
                        )
                    )
                ).all()
            )
            for artifact in artifacts:
                delete_file_if_present(artifact.storage_path)
                deleted_files += 1

    logger.info("Retention cleanup removed %s files", deleted_files)
    return deleted_files
