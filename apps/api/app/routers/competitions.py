from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.dependencies.auth import get_admin_user
from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.competitions import (
    create_competition,
    get_competition_by_slug,
    list_competitions,
    update_competition,
)
from apps.api.app.schemas.competitions import (
    CompetitionCreateRequest,
    CompetitionResponse,
    CompetitionUpdateRequest,
)
from packages.db.models import User

router = APIRouter(prefix="/competitions", tags=["competitions"])


@router.get("", response_model=list[CompetitionResponse])
def competitions(db: Session = Depends(get_db)) -> list[CompetitionResponse]:
    return [CompetitionResponse.model_validate(item) for item in list_competitions(db)]


@router.post("", response_model=CompetitionResponse, status_code=status.HTTP_201_CREATED)
def create_competition_endpoint(
    payload: CompetitionCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
) -> CompetitionResponse:
    existing = get_competition_by_slug(db, slug=payload.slug)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Competition slug already exists.",
        )

    competition = create_competition(
        db,
        payload=payload.model_dump(),
        created_by=admin_user.id,
    )
    db.commit()
    db.refresh(competition)
    return CompetitionResponse.model_validate(competition)


@router.get("/{slug}", response_model=CompetitionResponse)
def competition(slug: str, db: Session = Depends(get_db)) -> CompetitionResponse:
    item = get_competition_by_slug(db, slug=slug)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found.")

    return CompetitionResponse.model_validate(item)


@router.patch("/{slug}", response_model=CompetitionResponse)
def update_competition_endpoint(
    slug: str,
    payload: CompetitionUpdateRequest,
    db: Session = Depends(get_db),
    _admin_user: User = Depends(get_admin_user),
) -> CompetitionResponse:
    competition = get_competition_by_slug(db, slug=slug)
    if competition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competition not found.")

    updated = update_competition(
        db,
        competition=competition,
        payload=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(updated)
    return CompetitionResponse.model_validate(updated)
