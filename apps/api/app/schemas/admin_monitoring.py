from datetime import datetime

from pydantic import BaseModel

from apps.api.app.schemas.jobs import JobResponse
from apps.api.app.schemas.submissions import ScoreSummaryResponse


class AdminWorkerResponse(BaseModel):
    worker_id: str
    availability_status: str
    is_online: bool
    is_enabled: bool
    gpu_available: bool
    total_jobs: int
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    latest_job_status: str | None
    latest_job_at: datetime | None
    last_heartbeat_at: datetime | None


class AdminWorkerUpdateRequest(BaseModel):
    is_enabled: bool


class AdminTaskResponse(BaseModel):
    submission_id: str
    competition_id: str
    competition_slug: str
    competition_title: str
    participant_id: str
    participant_email: str
    participant_name: str
    submission_type: str
    submission_status: str
    source_original_filename: str
    created_at: datetime
    latest_job: JobResponse | None = None
    latest_score: ScoreSummaryResponse | None = None
