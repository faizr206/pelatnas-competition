from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from apps.api.app.config import get_settings
from apps.api.app.dependencies.auth import get_admin_user, get_current_user
from apps.api.app.dependencies.db import get_db
from apps.api.app.repositories.competitions import get_competition_by_slug
from apps.api.app.repositories.datasets import (
    get_dataset_by_id,
    get_next_dataset_version,
    list_datasets,
)
from apps.api.app.schemas.datasets import DatasetResponse
from packages.db.models import Dataset, User
from packages.security.upload_validation import validate_dataset_upload, validate_upload_size
from packages.storage.service import build_attachment_content_disposition, get_object, save_upload

router = APIRouter(tags=["datasets"])


@router.get("/competitions/{slug}/datasets", response_model=list[DatasetResponse])
def get_datasets(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DatasetResponse]:
    competition = get_competition_by_slug(db, slug=slug, current_user=current_user)
    if competition is None:
        raise HTTPException(status_code=404, detail="Competition not found.")
    return [
        DatasetResponse.model_validate(item)
        for item in list_datasets(db, competition_id=competition.id)
    ]


@router.post(
    "/competitions/{slug}/datasets",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    slug: str,
    name: str = Form(...),
    dataset_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
) -> DatasetResponse:
    competition = get_competition_by_slug(db, slug=slug, current_user=admin_user)
    if competition is None:
        raise HTTPException(status_code=404, detail="Competition not found.")

    version = get_next_dataset_version(db, competition_id=competition.id)
    settings = get_settings()
    validate_upload_size(
        dataset_file,
        max_bytes=settings.max_dataset_upload_bytes,
        label="dataset file",
    )
    validate_dataset_upload(dataset_file)

    stored_file = save_upload(
        settings.local_storage_root,
        category="datasets",
        competition_slug=competition.slug,
        filename=dataset_file.filename or f"{name}.bin",
        upload=dataset_file,
    )

    for existing in list_datasets(db, competition_id=competition.id):
        existing.is_active = False

    dataset = Dataset(
        competition_id=competition.id,
        name=name,
        version=version,
        storage_path=stored_file.absolute_path,
        checksum=stored_file.checksum,
        original_filename=stored_file.original_filename,
        content_type=stored_file.content_type,
        size_bytes=stored_file.size_bytes,
        is_active=True,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return DatasetResponse.model_validate(dataset)


@router.get("/datasets/{dataset_id}/download")
def download_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Response:
    dataset = get_dataset_by_id(db, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    stored = get_object(dataset.storage_path)
    return Response(
        content=stored.body,
        media_type=dataset.content_type,
        headers={
            "Content-Disposition": build_attachment_content_disposition(
                dataset.original_filename,
                fallback="dataset.bin",
            )
        },
    )
