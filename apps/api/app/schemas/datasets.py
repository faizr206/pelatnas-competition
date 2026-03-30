from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    competition_id: str
    name: str
    version: int
    storage_path: str
    checksum: str
    original_filename: str
    content_type: str
    size_bytes: int
    is_active: bool
    created_at: datetime
