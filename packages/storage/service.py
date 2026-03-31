from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


@dataclass(frozen=True)
class StoredFile:
    absolute_path: str
    checksum: str
    size_bytes: int
    content_type: str
    original_filename: str


def ensure_storage_root(storage_root: str) -> Path:
    root = Path(storage_root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def submission_artifact_dir(storage_root: str, submission_id: str) -> Path:
    root = ensure_storage_root(storage_root)
    artifact_dir = root / "artifacts" / submission_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return artifact_dir


def save_upload(
    storage_root: str,
    *,
    category: str,
    competition_slug: str,
    filename: str,
    upload: UploadFile,
) -> StoredFile:
    root = ensure_storage_root(storage_root)
    target_dir = root / category / competition_slug
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = filename.replace("/", "_").replace("\\", "_")
    target_path = target_dir / f"{uuid4()}-{safe_name}"
    digest = hashlib.sha256()

    with target_path.open("wb") as destination:
        upload.file.seek(0)
        while chunk := upload.file.read(1024 * 1024):
            digest.update(chunk)
            destination.write(chunk)

    return StoredFile(
        absolute_path=str(target_path),
        checksum=digest.hexdigest(),
        size_bytes=target_path.stat().st_size,
        content_type=upload.content_type or "application/octet-stream",
        original_filename=upload.filename or safe_name,
    )


def save_text_file(
    storage_root: str,
    *,
    category: str,
    competition_slug: str,
    filename: str,
    contents: str,
) -> str:
    root = ensure_storage_root(storage_root)
    target_dir = root / category / competition_slug
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = filename.replace("/", "_").replace("\\", "_")
    target_path = target_dir / f"{uuid4()}-{safe_name}"
    target_path.write_text(contents, encoding="utf-8")
    return str(target_path)


def copy_file_to_versioned_path(
    storage_root: str,
    *,
    category: str,
    competition_slug: str,
    version: int,
    source_path: str,
    original_filename: str,
) -> str:
    root = ensure_storage_root(storage_root)
    target_dir = root / category / competition_slug / f"v{version}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / original_filename.replace("/", "_").replace("\\", "_")
    shutil.copyfile(source_path, target_path)
    return str(target_path)


def delete_file_if_present(path: str) -> None:
    target = Path(path)
    if target.exists():
        target.unlink()
