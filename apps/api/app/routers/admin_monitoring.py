from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.dependencies.auth import get_admin_user
from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.jobs import get_latest_job_for_submission
from apps.api.app.repositories.scores import get_latest_score_for_submission
from apps.api.app.schemas.admin_monitoring import (
    AdminTaskResponse,
    AdminWorkerResponse,
    AdminWorkerUpdateRequest,
)
from apps.api.app.schemas.jobs import JobResponse
from apps.api.app.schemas.submissions import ScoreSummaryResponse
from packages.db.models import Competition, Job, Submission, User
from packages.workers.service import (
    list_worker_nodes,
    upsert_worker_node,
    worker_is_online,
)

router = APIRouter(prefix="/admin", tags=["admin-monitoring"])

ACTIVE_JOB_STATUSES = {"pending", "queued", "running", "collecting", "scoring"}


@router.get("/workers", response_model=list[AdminWorkerResponse])
def list_workers(
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[AdminWorkerResponse]:
    registry_workers = {worker.worker_id: worker for worker in list_worker_nodes(db)}
    jobs = list(
        db.scalars(
            select(Job).where(Job.worker_id.is_not(None)).order_by(Job.created_at.desc())
        ).all()
    )

    workers: dict[str, AdminWorkerResponse] = {}
    for job in jobs:
        if job.worker_id is None:
            continue
        summary = workers.get(job.worker_id)
        if summary is None:
            summary = AdminWorkerResponse(
                worker_id=job.worker_id,
                availability_status="idle",
                is_online=False,
                is_enabled=True,
                total_jobs=0,
                active_jobs=0,
                completed_jobs=0,
                failed_jobs=0,
                latest_job_status=job.status,
                latest_job_at=job.finished_at or job.started_at or job.queued_at or job.created_at,
                last_heartbeat_at=None,
            )
            workers[job.worker_id] = summary

        summary.total_jobs += 1
        if job.status in ACTIVE_JOB_STATUSES:
            summary.active_jobs += 1
        elif job.status == "completed":
            summary.completed_jobs += 1
        elif job.status == "failed":
            summary.failed_jobs += 1

    for worker_id, registry_worker in registry_workers.items():
        summary = workers.get(worker_id)
        if summary is None:
            summary = AdminWorkerResponse(
                worker_id=worker_id,
                availability_status="offline",
                is_online=False,
                is_enabled=registry_worker.is_enabled,
                total_jobs=0,
                active_jobs=0,
                completed_jobs=0,
                failed_jobs=0,
                latest_job_status=None,
                latest_job_at=None,
                last_heartbeat_at=registry_worker.last_heartbeat_at,
            )
            workers[worker_id] = summary
        summary.is_enabled = registry_worker.is_enabled
        summary.last_heartbeat_at = registry_worker.last_heartbeat_at
        summary.is_online = worker_is_online(registry_worker)

    results = list(workers.values())
    for summary in results:
        if not summary.is_enabled:
            summary.availability_status = "disabled"
        elif summary.is_online:
            summary.availability_status = "busy" if summary.active_jobs > 0 else "idle"
        else:
            summary.availability_status = "offline"

    return sorted(
        results,
        key=lambda item: (
            item.availability_status != "busy",
            item.latest_job_at is None,
            item.latest_job_at,
            item.worker_id,
        ),
        reverse=False,
    )


@router.patch("/workers/{worker_id}", response_model=AdminWorkerResponse)
def update_worker(
    worker_id: str,
    payload: AdminWorkerUpdateRequest,
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> AdminWorkerResponse:
    upsert_worker_node(db, worker_id=worker_id, is_enabled=payload.is_enabled)
    db.commit()

    workers = list_workers(_=_, db=db)
    for worker in workers:
        if worker.worker_id == worker_id:
            return worker
    raise HTTPException(status_code=404, detail="Worker not found.")


@router.get("/tasks", response_model=list[AdminTaskResponse])
def list_tasks(
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> list[AdminTaskResponse]:
    rows = db.execute(
        select(Submission, Competition, User)
        .join(Competition, Competition.id == Submission.competition_id)
        .join(User, User.id == Submission.user_id)
        .order_by(Submission.created_at.desc())
    ).all()

    tasks: list[AdminTaskResponse] = []
    for submission, competition, participant in rows:
        latest_job = get_latest_job_for_submission(db, submission_id=submission.id)
        latest_score = get_latest_score_for_submission(db, submission_id=submission.id)
        tasks.append(
            AdminTaskResponse(
                submission_id=submission.id,
                competition_id=competition.id,
                competition_slug=competition.slug,
                competition_title=competition.title,
                participant_id=participant.id,
                participant_email=participant.email,
                participant_name=participant.display_name,
                submission_type=submission.submission_type,
                submission_status=submission.status,
                source_original_filename=submission.source_original_filename,
                created_at=submission.created_at,
                latest_job=None if latest_job is None else JobResponse.model_validate(latest_job),
                latest_score=(
                    None
                    if latest_score is None
                    else ScoreSummaryResponse(
                        metric_name=latest_score.metric_name,
                        metric_value=latest_score.metric_value,
                        score_value=latest_score.score_value,
                        public_score_value=latest_score.public_score_value,
                        private_score_value=latest_score.private_score_value,
                        scoring_version=latest_score.scoring_version,
                    )
                ),
            )
        )

    return tasks
