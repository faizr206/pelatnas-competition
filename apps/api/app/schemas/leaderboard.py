from datetime import datetime

from pydantic import BaseModel


class LeaderboardEntryResponse(BaseModel):
    rank: int | None
    score_value: float
    user_id: str
    best_submission_id: str
    submission_created_at: datetime
    submitter_email: str
    submitter_name: str
