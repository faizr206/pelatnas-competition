from datetime import datetime

from pydantic import BaseModel, ConfigDict

from apps.api.app.schemas.jobs import JobResponse


class ScoreSummaryResponse(BaseModel):
    metric_name: str
    metric_value: float
    score_value: float
    scoring_version: str


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    competition_id: str
    phase_id: str
    user_id: str
    submission_type: str
    status: str
    source_archive_path: str
    source_original_filename: str
    source_content_type: str
    source_checksum: str
    source_size_bytes: int
    created_at: datetime
    latest_score: ScoreSummaryResponse | None = None
    latest_job: JobResponse | None = None


class SubmissionArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    artifact_type: str
    storage_path: str
    checksum: str | None
    size_bytes: int
    created_at: datetime
