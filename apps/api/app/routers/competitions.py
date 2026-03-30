from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.competitions import get_competition_by_slug, list_competitions
from apps.api.app.schemas.competitions import CompetitionResponse

router = APIRouter(prefix="/competitions", tags=["competitions"])


@router.get("", response_model=list[CompetitionResponse])
def competitions(db: Session = Depends(get_db)) -> list[CompetitionResponse]:
    return [CompetitionResponse.model_validate(item) for item in list_competitions(db)]


@router.get("/{slug}", response_model=CompetitionResponse)
def competition(slug: str, db: Session = Depends(get_db)) -> CompetitionResponse:
    item = get_competition_by_slug(db, slug=slug)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found.")

    return CompetitionResponse.model_validate(item)
