import os

from celery import Celery

from apps.worker.worker.job_handlers.submission_pipeline import process_submission_job

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("competition-worker", broker=redis_url, backend=redis_url)
celery_app.conf.update(
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)


@celery_app.task(name="submission.process")
def process_submission(job_id: str) -> str:
    return process_submission_job(job_id)
