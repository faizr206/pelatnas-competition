from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.dependencies.auth import get_current_user
from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.competitions import get_active_phase, get_competition_by_slug
from apps.api.app.repositories.submissions import create_submission, list_submissions_for_user
from apps.api.app.schemas.jobs import JobResponse
from apps.api.app.schemas.submissions import SubmissionCreateRequest, SubmissionResponse
from apps.api.app.services.jobs import create_and_enqueue_submission_job
from packages.db.models import User

router = APIRouter(prefix="/competitions/{slug}/submissions", tags=["submissions"])


@router.get("", response_model=list[SubmissionResponse])
def list_submissions(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SubmissionResponse]:
    competition = get_competition_by_slug(db, slug=slug)
    if competition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found.")

    submissions = list_submissions_for_user(
        db, competition_id=competition.id, user_id=current_user.id
    )
    return [SubmissionResponse.model_validate(item) for item in submissions]


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def submit(
    slug: str,
    payload: SubmissionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    competition = get_competition_by_slug(db, slug=slug)
    if competition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found.")

    phase = get_active_phase(db, competition_id=competition.id)
    if phase is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active phase.")

    submission = create_submission(
        db,
        competition_id=competition.id,
        phase_id=phase.id,
        user_id=current_user.id,
        submission_type=payload.submission_type,
        source_archive_path=payload.source_archive_path,
        manifest_path=payload.manifest_path,
    )
    job = create_and_enqueue_submission_job(db, submission_id=submission.id)
    db.commit()
    db.refresh(job)
    return JobResponse.model_validate(job)
