from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.dependencies.auth import get_current_user
from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.jobs import get_job_by_id
from apps.api.app.repositories.submissions import get_submission_by_id
from apps.api.app.schemas.jobs import JobResponse
from packages.db.models import User

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> JobResponse:
    job = get_job_by_id(db, job_id=job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    submission = get_submission_by_id(db, job.submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found.")
    if submission.user_id != _current_user.id and not _current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Job access denied.")

    return JobResponse.model_validate(job)
