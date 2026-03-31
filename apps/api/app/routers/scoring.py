from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from apps.api.app.config import get_settings
from apps.api.app.dependencies.auth import get_admin_user
from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.competitions import get_competition_by_slug
from apps.api.app.schemas.scoring import MetricTemplateResponse, ScoringConfigResponse
from packages.core.constants import ScoringDirection
from packages.db.models import User
from packages.scoring.service import (
    list_metric_templates,
    validate_metric_script,
    validate_solution_csv,
)
from packages.storage.service import save_text_file, save_upload

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
        metric_code = Path(competition.metric_script_path).read_text(encoding="utf-8")

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
) -> FileResponse:
    competition = get_competition_by_slug(db, slug=slug)
    if competition is None:
        raise HTTPException(status_code=404, detail="Competition not found.")
    if not competition.solution_path or not competition.solution_filename:
        raise HTTPException(status_code=404, detail="Solution file not found.")

    return FileResponse(
        Path(competition.solution_path),
        filename=competition.solution_filename,
        media_type="text/csv",
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
    if solution_file is None and not competition.solution_path:
        raise HTTPException(
            status_code=400,
            detail="Upload solution.csv before saving scoring configuration.",
        )

    settings = get_settings()
    metric_path = save_text_file(
        settings.local_storage_root,
        category="scoring",
        competition_slug=competition.slug,
        filename="custom_metric.py",
        contents=metric_code,
    )
    validate_metric_script(metric_path)

    if solution_file is not None:
        stored_solution = save_upload(
            settings.local_storage_root,
            category="solutions",
            competition_slug=competition.slug,
            filename=solution_file.filename or "solution.csv",
            upload=solution_file,
        )
        validate_solution_csv(stored_solution.absolute_path)
        competition.solution_path = stored_solution.absolute_path
        competition.solution_filename = stored_solution.original_filename

    competition.scoring_metric = metric_name
    competition.scoring_direction = scoring_direction
    competition.metric_script_path = metric_path
    competition.metric_script_filename = "custom_metric.py"
    db.commit()
    db.refresh(competition)

    return get_scoring_config(slug=slug, db=db, _admin_user=_admin_user)
