from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class SubmissionCreateRequest(BaseModel):
    submission_type: Literal["file"] = "file"
    source_archive_path: str = "phase0/source.zip"
    manifest_path: str = "phase0/manifest.json"


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    competition_id: str
    phase_id: str
    user_id: str
    submission_type: str
    status: str
    source_archive_path: str
    manifest_path: str
    created_at: datetime
