import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.config import get_settings
from apps.api.app.dependencies.auth import get_admin_user
from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.competitions import get_competition_by_slug
from apps.api.app.schemas.scoring import (
    MetricTemplateResponse,
    RescoreSubmissionsResponse,
    ScoringConfigResponse,
)
from apps.api.app.services.jobs import create_submission_job, enqueue_submission_job
from packages.core.constants import ScoringDirection, SubmissionStatus
from packages.db.models import Submission, User
from packages.scoring.service import (
    list_metric_templates,
    validate_metric_script,
    validate_solution_csv,
)
from packages.security.upload_validation import validate_csv_upload, validate_upload_size
from packages.storage.service import (
    build_attachment_content_disposition,
    get_object,
    get_object_text,
    save_text_file,
    save_upload,
)

router = APIRouter(tags=["scoring"])


@router.get(
    "/competitions/{slug}/scoring-config",
    response_model=ScoringConfigResponse,
)
def get_scoring_config(
    slug: str,
    db: Session = Depends(get_db),
    _admin_user: User = Depends(get_admin_user),
) -> ScoringConfigResponse:
    competition = get_competition_by_slug(db, slug=slug)
    if competition is None:
        raise HTTPException(status_code=404, detail="Competition not found.")

    metric_code = None
    if competition.metric_script_path:
        try:
            metric_code = get_object_text(competition.metric_script_path)
        except FileNotFoundError:
            competition.metric_script_path = None
            competition.metric_script_filename = None
            db.commit()
            db.refresh(competition)

    templates = [
        MetricTemplateResponse(
            name=template.name,
            title=template.title,
            description=template.description,
            code=template.code,
            default_metric_name=template.default_metric_name,
            default_scoring_direction=template.default_scoring_direction,
        )
        for template in list_metric_templates()
    ]
    return ScoringConfigResponse(
        competition_id=competition.id,
        submission_mode=competition.submission_mode,
        scoring_metric=competition.scoring_metric,
        scoring_direction=competition.scoring_direction,
        solution_filename=competition.solution_filename,
        metric_script_filename=competition.metric_script_filename,
        metric_code=metric_code,
        templates=templates,
    )


@router.get("/competitions/{slug}/solution-file")
def get_solution_file(
    slug: str,
    db: Session = Depends(get_db),
    _admin_user: User = Depends(get_admin_user),
) -> Response:
    competition = get_competition_by_slug(db, slug=slug)
    if competition is None:
        raise HTTPException(status_code=404, detail="Competition not found.")
    if not competition.solution_path or not competition.solution_filename:
        raise HTTPException(status_code=404, detail="Solution file not found.")

    try:
        stored = get_object(competition.solution_path)
    except FileNotFoundError as exc:
        competition.solution_path = None
        competition.solution_filename = None
        db.commit()
        raise HTTPException(status_code=404, detail="Solution file not found.") from exc
    return Response(
        content=stored.body,
        media_type="text/csv",
        headers={
            "Content-Disposition": build_attachment_content_disposition(
                competition.solution_filename,
                fallback="solution.csv",
            )
        },
    )


@router.post(
    "/competitions/{slug}/rescore-submissions",
    response_model=RescoreSubmissionsResponse,
)
def rescore_submissions(
    slug: str,
    db: Session = Depends(get_db),
    _admin_user: User = Depends(get_admin_user),
) -> RescoreSubmissionsResponse:
    competition = get_competition_by_slug(db, slug=slug)
    if competition is None:
        raise HTTPException(status_code=404, detail="Competition not found.")
    if not competition.metric_script_path:
        raise HTTPException(status_code=400, detail="Save scoring configuration before rescoring.")
    if competition.submission_mode == "prediction_file" and not competition.solution_path:
        raise HTTPException(
            status_code=400,
            detail="Upload solution.csv before rescoring prediction-file submissions.",
        )

    submissions = list(
        db.scalars(
            select(Submission)
            .where(Submission.competition_id == competition.id)
            .order_by(Submission.created_at.asc())
        ).all()
    )
    if not submissions:
        return RescoreSubmissionsResponse(queued_submission_count=0, job_ids=[])

    job_ids: list[str] = []
    for submission in submissions:
        submission.status = SubmissionStatus.PENDING.value
        job = create_submission_job(db, submission_id=submission.id)
        job_ids.append(job.id)

    db.commit()

    for job_id in job_ids:
        enqueue_submission_job(db, job_id=job_id)

    db.commit()
    return RescoreSubmissionsResponse(
        queued_submission_count=len(job_ids),
        job_ids=job_ids,
    )


@router.put(
    "/competitions/{slug}/scoring-config",
    response_model=ScoringConfigResponse,
)
async def update_scoring_config(
    slug: str,
    metric_name: str = Form(...),
    scoring_direction: str = Form(...),
    metric_code: str = Form(...),
    solution_file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    _admin_user: User = Depends(get_admin_user),
) -> ScoringConfigResponse:
    competition = get_competition_by_slug(db, slug=slug)
    if competition is None:
        raise HTTPException(status_code=404, detail="Competition not found.")
    if scoring_direction not in {
        ScoringDirection.MAX.value,
        ScoringDirection.MIN.value,
    }:
        raise HTTPException(status_code=400, detail="Scoring direction must be max or min.")
    if competition.solution_path is not None:
        try:
            get_object(competition.solution_path)
        except FileNotFoundError:
            competition.solution_path = None
            competition.solution_filename = None
    if competition.submission_mode == "prediction_file":
        if solution_file is None and not competition.solution_path:
            raise HTTPException(
                status_code=400,
                detail="Upload solution.csv before saving scoring configuration.",
            )
    elif competition.submission_mode != "code_submission":
        raise HTTPException(status_code=400, detail="Unsupported competition submission mode.")

    settings = get_settings()
    with tempfile.NamedTemporaryFile(suffix=".py") as metric_handle:
        metric_handle.write(metric_code.encode("utf-8"))
        metric_handle.flush()
        validate_metric_script(metric_handle.name, submission_mode=competition.submission_mode)
    metric_path = save_text_file(
        settings.local_storage_root,
        category="scoring",
        competition_slug=competition.slug,
        filename="custom_metric.py",
        contents=metric_code,
    )

    if solution_file is not None:
        validate_upload_size(
            solution_file,
            max_bytes=settings.max_solution_upload_bytes,
            label="solution file",
        )
        validate_csv_upload(solution_file, label="solution file")
        with tempfile.NamedTemporaryFile(suffix=".csv") as solution_handle:
            solution_file.file.seek(0)
            solution_handle.write(solution_file.file.read())
            solution_handle.flush()
            validate_solution_csv(solution_handle.name)
            solution_file.file.seek(0)
        stored_solution = save_upload(
            settings.local_storage_root,
            category="solutions",
            competition_slug=competition.slug,
            filename=solution_file.filename or "solution.csv",
            upload=solution_file,
        )
        competition.solution_path = stored_solution.absolute_path
        competition.solution_filename = stored_solution.original_filename

    competition.scoring_metric = metric_name
    competition.scoring_direction = scoring_direction
    competition.metric_script_path = metric_path
    competition.metric_script_filename = "custom_metric.py"
    db.commit()
    db.refresh(competition)

    return get_scoring_config(slug=slug, db=db, _admin_user=_admin_user)
