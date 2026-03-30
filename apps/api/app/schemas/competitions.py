from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CompetitionPhaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    starts_at: datetime
    ends_at: datetime
    submission_limit_per_day: int
    scoring_version: str
    rules_version: str


class CompetitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    title: str
    description: str
    visibility: str
    status: str
    phases: list[CompetitionPhaseResponse]
