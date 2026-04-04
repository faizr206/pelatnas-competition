from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.config import get_settings
from apps.api.app.dependencies.auth import get_current_user
from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.competitions import get_active_phase, get_competition_by_slug
from apps.api.app.repositories.jobs import get_latest_job_for_submission
from apps.api.app.repositories.scores import get_latest_score_for_submission
from apps.api.app.repositories.submissions import (
    count_submissions_for_day,
    create_submission,
    get_submission_by_id,
    list_submissions_for_user,
)
from apps.api.app.schemas.jobs import JobResponse
from apps.api.app.schemas.submissions import (
    ScoreSummaryResponse,
    SubmissionArtifactResponse,
    SubmissionResponse,
)
from apps.api.app.services.jobs import create_submission_job, enqueue_submission_job
from packages.core.constants import SubmissionType
from packages.core.time import utcnow
from packages.db.models import CompetitionPhase, Submission, SubmissionArtifact, User
from packages.security.upload_validation import (
    validate_csv_upload,
    validate_notebook_upload,
    validate_upload_size,
)
from packages.storage.service import get_object, save_upload

router = APIRouter(tags=["submissions"])


@router.get("/competitions/{slug}/submissions", response_model=list[SubmissionResponse])
def list_submissions(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SubmissionResponse]:
    competition = get_competition_by_slug(db, slug=slug)
    if competition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found.")

    submissions = list_submissions_for_user(
        db,
        competition_id=competition.id,
        user_id=current_user.id,
    )
    return [_serialize_submission(db=db, submission=submission) for submission in submissions]


@router.post("/competitions/{slug}/submissions", response_model=JobResponse, status_code=202)
async def submit(
    slug: str,
    submission_type: str = Form(...),
    source_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    competition = get_competition_by_slug(db, slug=slug)
    if competition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found.")

    phase = get_active_phase(db, competition_id=competition.id)
    if phase is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active phase.")
    now = utcnow()
    phase_starts_at = _as_utc(phase.starts_at)
    phase_ends_at = _as_utc(phase.ends_at)
    if phase_starts_at > now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submissions are not open for this competition yet.",
        )
    is_late_submission = phase_ends_at < now

    if submission_type not in {SubmissionType.CSV.value, SubmissionType.NOTEBOOK.value}:
        raise HTTPException(status_code=400, detail="Submission type must be csv or notebook.")
    if (
        competition.submission_mode == "prediction_file"
        and submission_type != SubmissionType.CSV.value
    ):
        raise HTTPException(
            status_code=400,
            detail="This competition only accepts submission.csv prediction files.",
        )
    if (
        competition.submission_mode == "code_submission"
        and submission_type != SubmissionType.NOTEBOOK.value
    ):
        raise HTTPException(
            status_code=400,
            detail="This competition only accepts notebook code submissions.",
        )

    if submission_type == SubmissionType.CSV.value and not competition.allow_csv_submissions:
        raise HTTPException(status_code=400, detail="CSV submissions are disabled.")
    if (
        submission_type == SubmissionType.NOTEBOOK.value
        and not competition.allow_notebook_submissions
    ):
        raise HTTPException(status_code=400, detail="Notebook submissions are disabled.")

    submission_count = count_submissions_for_day(
        db,
        competition_id=competition.id,
        user_id=current_user.id,
    )
    if submission_count >= competition.max_submissions_per_day:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily submission limit reached.",
        )

    settings = get_settings()
    validate_upload_size(
        source_file,
        max_bytes=settings.max_submission_upload_bytes,
        label="submission file",
    )
    if submission_type == SubmissionType.CSV.value:
        validate_csv_upload(source_file, label="submission file")
    else:
        validate_notebook_upload(source_file, label="submission file")

    stored_file = save_upload(
        settings.local_storage_root,
        category="submissions",
        competition_slug=competition.slug,
        filename=source_file.filename or "submission.bin",
        upload=source_file,
    )
    submission = create_submission(
        db,
        competition_id=competition.id,
        phase_id=phase.id,
        user_id=current_user.id,
        submission_type=submission_type,
        source_archive_path=stored_file.absolute_path,
        manifest_path=None,
        source_original_filename=stored_file.original_filename,
        source_content_type=stored_file.content_type,
        source_checksum=stored_file.checksum,
        source_size_bytes=stored_file.size_bytes,
        is_late_submission=is_late_submission,
    )
    job = create_submission_job(db, submission_id=submission.id)
    db.commit()
    db.refresh(job)
    job = enqueue_submission_job(db, job_id=job.id)
    db.commit()
    db.refresh(job)
    return JobResponse.model_validate(job)


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubmissionResponse:
    submission = _get_visible_submission(
        db=db,
        submission_id=submission_id,
        current_user=current_user,
    )
    return _serialize_submission(db=db, submission=submission)


@router.get(
    "/submissions/{submission_id}/artifacts", response_model=list[SubmissionArtifactResponse]
)
def list_submission_artifacts(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SubmissionArtifactResponse]:
    _ = _get_visible_submission(db=db, submission_id=submission_id, current_user=current_user)
    artifacts = list(
        db.scalars(
            select(SubmissionArtifact)
            .where(SubmissionArtifact.submission_id == submission_id)
            .order_by(SubmissionArtifact.created_at.asc())
        ).all()
    )
    return [SubmissionArtifactResponse.model_validate(item) for item in artifacts]


@router.get("/submissions/{submission_id}/logs")
def get_submission_logs(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    _ = _get_visible_submission(db=db, submission_id=submission_id, current_user=current_user)
    artifact = db.scalar(
        select(SubmissionArtifact)
        .where(SubmissionArtifact.submission_id == submission_id)
        .where(SubmissionArtifact.artifact_type == "stdout.log")
        .order_by(SubmissionArtifact.created_at.desc())
    )
    if artifact is None:
        raise HTTPException(status_code=404, detail="No log artifact found.")
    stored = get_object(artifact.storage_path)
    return Response(content=stored.body, media_type="text/plain; charset=utf-8")


def _get_visible_submission(
    *,
    db: Session,
    submission_id: str,
    current_user: User,
) -> Submission:
    submission = get_submission_by_id(db, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found.")
    if submission.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Submission access denied.")
    return submission


def _serialize_submission(*, db: Session, submission: Submission) -> SubmissionResponse:
    latest_score = get_latest_score_for_submission(db, submission_id=submission.id)
    latest_job = get_latest_job_for_submission(db, submission_id=submission.id)
    phase = db.get(CompetitionPhase, submission.phase_id)
    phase_has_ended = phase is not None and _as_utc(phase.ends_at) < utcnow()
    return SubmissionResponse(
        id=submission.id,
        competition_id=submission.competition_id,
        phase_id=submission.phase_id,
        user_id=submission.user_id,
        submission_type=submission.submission_type,
        status=submission.status,
        source_archive_path=submission.source_archive_path,
        source_original_filename=submission.source_original_filename,
        source_content_type=submission.source_content_type,
        source_checksum=submission.source_checksum,
        source_size_bytes=submission.source_size_bytes,
        is_late_submission=submission.is_late_submission,
        created_at=submission.created_at,
        latest_score=(
            None
            if latest_score is None
            else ScoreSummaryResponse(
                metric_name=latest_score.metric_name,
                metric_value=latest_score.metric_value,
                score_value=(
                    latest_score.private_score_value
                    if phase_has_ended
                    else latest_score.public_score_value
                ),
                public_score_value=latest_score.public_score_value,
                private_score_value=latest_score.private_score_value,
                scoring_version=latest_score.scoring_version,
            )
        ),
        latest_job=None if latest_job is None else JobResponse.model_validate(latest_job),
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
