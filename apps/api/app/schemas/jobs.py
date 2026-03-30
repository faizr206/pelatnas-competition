from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    submission_id: str
    job_type: str
    status: str
    queued_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    worker_id: str | None
    retry_count: int
    failure_reason: str | None
