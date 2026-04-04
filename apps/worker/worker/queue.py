import os

from celery import Celery, Task
from celery.signals import heartbeat_sent, worker_ready

from apps.worker.worker.job_handlers.retention_cleanup import cleanup_retention_targets
from apps.worker.worker.job_handlers.submission_pipeline import process_submission_job
from apps.worker.worker.utils.gpu import detect_gpu_available
from packages.workers.service import heartbeat_worker, is_worker_enabled

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
worker_id = os.getenv("WORKER_ID", "worker-local")

celery_app = Celery("competition-worker", broker=redis_url, backend=redis_url)
celery_app.conf.update(
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)


@worker_ready.connect
def _record_worker_ready(**_: object) -> None:
    heartbeat_worker(worker_id, gpu_available=detect_gpu_available())


@heartbeat_sent.connect
def _record_worker_heartbeat(**_: object) -> None:
    heartbeat_worker(worker_id, gpu_available=detect_gpu_available())


@celery_app.task(bind=True, name="submission.process", max_retries=None)
def process_submission_task(self: Task, job_id: str) -> str:
    if not is_worker_enabled(worker_id):
        raise self.retry(countdown=5)
    return process_submission_job(job_id)


@celery_app.task(name="retention.cleanup")
def retention_cleanup_task() -> int:
    return cleanup_retention_targets()
