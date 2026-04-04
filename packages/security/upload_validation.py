from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile, status

ALLOWED_CSV_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "text/plain",
    "application/octet-stream",
}

ALLOWED_NOTEBOOK_CONTENT_TYPES = {
    "application/x-ipynb+json",
    "application/json",
    "text/plain",
    "application/octet-stream",
}

ALLOWED_DATASET_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".txt",
    ".json",
    ".jsonl",
    ".zip",
    ".gz",
    ".bz2",
    ".xz",
    ".parquet",
}

ALLOWED_DATASET_CONTENT_TYPES = {
    "text/csv",
    "text/tab-separated-values",
    "text/plain",
    "application/json",
    "application/x-ndjson",
    "application/zip",
    "application/gzip",
    "application/x-gzip",
    "application/x-bzip2",
    "application/x-xz",
    "application/vnd.apache.parquet",
    "application/octet-stream",
}


def validate_upload_size(
    upload: UploadFile,
    *,
    max_bytes: int,
    label: str,
) -> None:
    try:
        upload.file.seek(0, 2)
        size_bytes = upload.file.tell()
        upload.file.seek(0)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read {label} size.",
        ) from exc

    if size_bytes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label.capitalize()} must not be empty.",
        )
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"{label.capitalize()} exceeds the maximum allowed size.",
        )


def validate_csv_upload(upload: UploadFile, *, label: str) -> None:
    extension = _normalized_extension(upload.filename)
    if extension != ".csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label.capitalize()} must be a .csv file.",
        )
    if not _content_type_allowed(upload, ALLOWED_CSV_CONTENT_TYPES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label.capitalize()} must use a CSV content type.",
        )


def validate_notebook_upload(upload: UploadFile, *, label: str) -> None:
    extension = _normalized_extension(upload.filename)
    if extension != ".ipynb":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label.capitalize()} must be a .ipynb file.",
        )
    if not _content_type_allowed(upload, ALLOWED_NOTEBOOK_CONTENT_TYPES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label.capitalize()} must use a notebook content type.",
        )


def validate_dataset_upload(upload: UploadFile) -> None:
    extension = _normalized_extension(upload.filename)
    if extension not in ALLOWED_DATASET_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset file type is not allowed.",
        )
    if not _content_type_allowed(upload, ALLOWED_DATASET_CONTENT_TYPES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset content type is not allowed.",
        )


def _normalized_extension(filename: str | None) -> str:
    if not filename:
        return ""
    return Path(filename).suffix.lower()


def _content_type_allowed(upload: UploadFile, allowed_content_types: set[str]) -> bool:
    content_type = (upload.content_type or "application/octet-stream").lower()
    return content_type in allowed_content_types
