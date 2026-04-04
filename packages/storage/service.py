from __future__ import annotations

import hashlib
import mimetypes
import re
import tempfile
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from fastapi import UploadFile

from apps.api.app.config import get_settings


@dataclass(frozen=True)
class StoredFile:
    absolute_path: str
    checksum: str
    size_bytes: int
    content_type: str
    original_filename: str


@dataclass(frozen=True)
class StorageObject:
    body: bytes
    content_type: str
    size_bytes: int


_UNSAFE_DOWNLOAD_FILENAME_RE = re.compile(r'[\r\n"]+')


class StorageBackend:
    def save_upload(
        self,
        *,
        category: str,
        competition_slug: str,
        filename: str,
        upload: UploadFile,
    ) -> StoredFile:
        raise NotImplementedError

    def save_text_file(
        self,
        *,
        category: str,
        competition_slug: str,
        filename: str,
        contents: str,
    ) -> str:
        raise NotImplementedError

    def save_local_file(
        self,
        *,
        category: str,
        competition_slug: str,
        filename: str,
        source_path: str,
        content_type: str | None = None,
    ) -> StoredFile:
        raise NotImplementedError

    def get_object(self, key: str) -> StorageObject:
        raise NotImplementedError

    def read_text(self, key: str) -> str:
        return self.get_object(key).body.decode("utf-8")

    def download_file(self, key: str, target_path: str) -> str:
        raise NotImplementedError

    def delete_file_if_present(self, key: str) -> None:
        raise NotImplementedError


class S3StorageBackend(StorageBackend):
    def __init__(
        self,
        *,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str,
        secure: bool,
    ) -> None:
        self.bucket = bucket
        scheme = "https" if secure else "http"
        normalized_endpoint = endpoint_url
        if "://" not in normalized_endpoint:
            normalized_endpoint = f"{scheme}://{normalized_endpoint}"
        self.client = boto3.client(
            "s3",
            endpoint_url=normalized_endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        for attempt in range(10):
            try:
                self.client.head_bucket(Bucket=self.bucket)
                return
            except EndpointConnectionError:
                if attempt == 9:
                    raise
                time.sleep(1)
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code")
                if error_code in {"404", "NoSuchBucket"}:
                    try:
                        self.client.create_bucket(Bucket=self.bucket)
                        return
                    except Exception:
                        if attempt == 9:
                            raise
                        time.sleep(1)
                        continue
                if attempt == 9:
                    raise
                time.sleep(1)

    def save_upload(
        self,
        *,
        category: str,
        competition_slug: str,
        filename: str,
        upload: UploadFile,
    ) -> StoredFile:
        with tempfile.NamedTemporaryFile(delete=False) as handle:
            temp_path = Path(handle.name)
        try:
            digest = hashlib.sha256()
            size_bytes = 0
            with temp_path.open("wb") as destination:
                upload.file.seek(0)
                while chunk := upload.file.read(1024 * 1024):
                    digest.update(chunk)
                    size_bytes += len(chunk)
                    destination.write(chunk)
            return self._upload_path(
                source_path=temp_path,
                category=category,
                competition_slug=competition_slug,
                filename=filename,
                checksum=digest.hexdigest(),
                size_bytes=size_bytes,
                content_type=upload.content_type or "application/octet-stream",
                original_filename=upload.filename or filename,
            )
        finally:
            temp_path.unlink(missing_ok=True)

    def save_text_file(
        self,
        *,
        category: str,
        competition_slug: str,
        filename: str,
        contents: str,
    ) -> str:
        payload = contents.encode("utf-8")
        stored = self._put_bytes(
            category=category,
            competition_slug=competition_slug,
            filename=filename,
            payload=payload,
            content_type="text/plain; charset=utf-8",
            original_filename=filename,
        )
        return stored.absolute_path

    def save_local_file(
        self,
        *,
        category: str,
        competition_slug: str,
        filename: str,
        source_path: str,
        content_type: str | None = None,
    ) -> StoredFile:
        path = Path(source_path)
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        guessed_type = (
            content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        )
        return self._upload_path(
            source_path=path,
            category=category,
            competition_slug=competition_slug,
            filename=filename,
            checksum=digest.hexdigest(),
            size_bytes=path.stat().st_size,
            content_type=guessed_type,
            original_filename=filename,
        )

    def _upload_path(
        self,
        *,
        source_path: Path,
        category: str,
        competition_slug: str,
        filename: str,
        checksum: str,
        size_bytes: int,
        content_type: str,
        original_filename: str,
    ) -> StoredFile:
        key = _build_object_key(
            category=category,
            competition_slug=competition_slug,
            filename=filename,
        )
        with source_path.open("rb") as handle:
            self.client.upload_fileobj(
                handle,
                self.bucket,
                key,
                ExtraArgs={"ContentType": content_type},
            )
        return StoredFile(
            absolute_path=key,
            checksum=checksum,
            size_bytes=size_bytes,
            content_type=content_type,
            original_filename=original_filename,
        )

    def _put_bytes(
        self,
        *,
        category: str,
        competition_slug: str,
        filename: str,
        payload: bytes,
        content_type: str,
        original_filename: str,
    ) -> StoredFile:
        key = _build_object_key(
            category=category,
            competition_slug=competition_slug,
            filename=filename,
        )
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=payload,
            ContentType=content_type,
        )
        return StoredFile(
            absolute_path=key,
            checksum=hashlib.sha256(payload).hexdigest(),
            size_bytes=len(payload),
            content_type=content_type,
            original_filename=original_filename,
        )

    def get_object(self, key: str) -> StorageObject:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
                raise FileNotFoundError(key) from exc
            raise
        body = response["Body"].read()
        return StorageObject(
            body=body,
            content_type=response.get("ContentType") or "application/octet-stream",
            size_bytes=len(body),
        )

    def download_file(self, key: str, target_path: str) -> str:
        path = Path(target_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.client.download_file(self.bucket, key, str(path))
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
                raise FileNotFoundError(key) from exc
            raise
        return str(path)

    def delete_file_if_present(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except ClientError:
            return


class MemoryStorageBackend(StorageBackend):
    def __init__(self) -> None:
        self.objects: dict[str, StorageObject] = {}

    def save_upload(
        self,
        *,
        category: str,
        competition_slug: str,
        filename: str,
        upload: UploadFile,
    ) -> StoredFile:
        upload.file.seek(0)
        payload = upload.file.read()
        return self._put_bytes(
            category=category,
            competition_slug=competition_slug,
            filename=filename,
            payload=payload,
            content_type=upload.content_type or "application/octet-stream",
            original_filename=upload.filename or filename,
        )

    def save_text_file(
        self,
        *,
        category: str,
        competition_slug: str,
        filename: str,
        contents: str,
    ) -> str:
        stored = self._put_bytes(
            category=category,
            competition_slug=competition_slug,
            filename=filename,
            payload=contents.encode("utf-8"),
            content_type="text/plain; charset=utf-8",
            original_filename=filename,
        )
        return stored.absolute_path

    def save_local_file(
        self,
        *,
        category: str,
        competition_slug: str,
        filename: str,
        source_path: str,
        content_type: str | None = None,
    ) -> StoredFile:
        path = Path(source_path)
        payload = path.read_bytes()
        guessed_type = (
            content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        )
        return self._put_bytes(
            category=category,
            competition_slug=competition_slug,
            filename=filename,
            payload=payload,
            content_type=guessed_type,
            original_filename=filename,
        )

    def _put_bytes(
        self,
        *,
        category: str,
        competition_slug: str,
        filename: str,
        payload: bytes,
        content_type: str,
        original_filename: str,
    ) -> StoredFile:
        key = _build_object_key(
            category=category,
            competition_slug=competition_slug,
            filename=filename,
        )
        self.objects[key] = StorageObject(
            body=payload,
            content_type=content_type,
            size_bytes=len(payload),
        )
        return StoredFile(
            absolute_path=key,
            checksum=hashlib.sha256(payload).hexdigest(),
            size_bytes=len(payload),
            content_type=content_type,
            original_filename=original_filename,
        )

    def get_object(self, key: str) -> StorageObject:
        if key not in self.objects:
            raise FileNotFoundError(key)
        return self.objects[key]

    def download_file(self, key: str, target_path: str) -> str:
        path = Path(target_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.get_object(key).body)
        return str(path)

    def delete_file_if_present(self, key: str) -> None:
        self.objects.pop(key, None)


def _build_object_key(*, category: str, competition_slug: str, filename: str) -> str:
    safe_name = filename.replace("/", "_").replace("\\", "_")
    return f"{category}/{competition_slug}/{uuid4()}-{safe_name}"


def build_attachment_content_disposition(filename: str, *, fallback: str = "download.bin") -> str:
    safe_name = filename.replace("/", "_").replace("\\", "_")
    safe_name = _UNSAFE_DOWNLOAD_FILENAME_RE.sub("", safe_name).strip()
    if not safe_name:
        safe_name = fallback
    return f'attachment; filename="{safe_name}"'


@lru_cache
def get_storage() -> StorageBackend:
    settings = get_settings()
    if settings.garage_endpoint == "memory://":
        return MemoryStorageBackend()
    return S3StorageBackend(
        endpoint_url=settings.garage_endpoint,
        access_key=settings.garage_access_key,
        secret_key=settings.garage_secret_key,
        bucket=settings.garage_bucket,
        region=settings.garage_region,
        secure=settings.garage_secure,
    )


def ensure_storage_ready() -> None:
    get_storage()


def save_upload(
    storage_root: str,
    *,
    category: str,
    competition_slug: str,
    filename: str,
    upload: UploadFile,
) -> StoredFile:
    del storage_root
    return get_storage().save_upload(
        category=category,
        competition_slug=competition_slug,
        filename=filename,
        upload=upload,
    )


def save_text_file(
    storage_root: str,
    *,
    category: str,
    competition_slug: str,
    filename: str,
    contents: str,
) -> str:
    del storage_root
    return get_storage().save_text_file(
        category=category,
        competition_slug=competition_slug,
        filename=filename,
        contents=contents,
    )


def save_local_file(
    *,
    category: str,
    competition_slug: str,
    filename: str,
    source_path: str,
    content_type: str | None = None,
) -> StoredFile:
    return get_storage().save_local_file(
        category=category,
        competition_slug=competition_slug,
        filename=filename,
        source_path=source_path,
        content_type=content_type,
    )


def get_object_bytes(path: str) -> bytes:
    return get_storage().get_object(path).body


def get_object_text(path: str) -> str:
    return get_storage().read_text(path)


def get_object(path: str) -> StorageObject:
    return get_storage().get_object(path)


def download_file_to_path(path: str, target_path: str) -> str:
    return get_storage().download_file(path, target_path)


def delete_file_if_present(path: str) -> None:
    get_storage().delete_file_if_present(path)


def write_stream_to_file(stream: BinaryIO, target_path: str) -> tuple[str, str, int]:
    path = Path(target_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size_bytes = 0
    with path.open("wb") as destination:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size_bytes += len(chunk)
            destination.write(chunk)
    return str(path), digest.hexdigest(), size_bytes
