from sqlalchemy.orm import Session

from apps.api.app.repositories.jobs import create_job
from packages.core.constants import JobStatus
from packages.db.models import Job


def create_and_enqueue_submission_job(db: Session, *, submission_id: str) -> Job:
    job = create_job(
        db,
        submission_id=submission_id,
        job_type="submission_pipeline",
        status=JobStatus.PENDING,
    )
    db.flush()

    from apps.worker.worker.queue import celery_app

    async_result = celery_app.send_task("submission.process", args=[job.id])
    job.status = JobStatus.QUEUED.value
    job.celery_task_id = async_result.id
    db.flush()
    return job
