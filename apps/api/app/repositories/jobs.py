from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.core.constants import JobStatus
from packages.db.models import Job


def get_job_by_id(db: Session, job_id: str) -> Job | None:
    return db.scalar(select(Job).where(Job.id == job_id))


def create_job(
    db: Session,
    *,
    submission_id: str,
    job_type: str,
    status: JobStatus,
) -> Job:
    job = Job(
        submission_id=submission_id,
        job_type=job_type,
        status=status.value,
        queued_at=datetime.now(UTC),
    )
    db.add(job)
    db.flush()
    return job
