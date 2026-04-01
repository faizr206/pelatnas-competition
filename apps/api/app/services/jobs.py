from sqlalchemy.orm import Session

from apps.api.app.repositories.jobs import create_job, get_job_by_id
from packages.core.constants import JobStatus
from packages.db.models import Job


def create_submission_job(db: Session, *, submission_id: str) -> Job:
    return create_job(
        db,
        submission_id=submission_id,
        job_type="submission_pipeline",
        status=JobStatus.PENDING,
    )


def enqueue_submission_job(db: Session, *, job_id: str) -> Job:
    job = get_job_by_id(db, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} was not found before enqueue.")

    from apps.worker.worker.queue import process_submission_task

    async_result = process_submission_task.apply_async(args=[job.id])
    db.expire_all()
    latest_job = get_job_by_id(db, job_id)
    if latest_job is None:
        raise ValueError(f"Job {job_id} was not found after enqueue.")

    latest_job.celery_task_id = async_result.id
    if latest_job.status == JobStatus.PENDING.value:
        latest_job.status = JobStatus.QUEUED.value
    db.flush()
    return latest_job
