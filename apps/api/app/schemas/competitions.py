from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompetitionPhaseCreateRequest(BaseModel):
    name: str = "main"
    starts_at: datetime
    ends_at: datetime
    submission_limit_per_day: int = Field(default=5, ge=1)
    scoring_version: str = "v1"
    rules_version: str = "v1"


class CompetitionCreateRequest(BaseModel):
    slug: str
    title: str
    description: str
    visibility: str = "public"
    status: str = "draft"
    submission_mode: str = "prediction_file"
    scoring_metric: str = "row_count"
    scoring_direction: str = "max"
    best_submission_rule: str = "best_score"
    max_submissions_per_day: int = Field(default=5, ge=1)
    max_runtime_minutes: int = Field(default=20, ge=1)
    max_memory_mb: int = Field(default=4096, ge=256)
    max_cpu: int = Field(default=2, ge=1)
    allow_csv_submissions: bool = True
    allow_notebook_submissions: bool = True
    source_retention_days: int = Field(default=30, ge=1)
    log_retention_days: int = Field(default=14, ge=1)
    artifact_retention_days: int = Field(default=14, ge=1)
    private_leaderboard_opens_at: datetime | None = None
    phase: CompetitionPhaseCreateRequest


class CompetitionUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    visibility: str | None = None
    status: str | None = None
    submission_mode: str | None = None
    scoring_metric: str | None = None
    scoring_direction: str | None = None
    best_submission_rule: str | None = None
    max_submissions_per_day: int | None = Field(default=None, ge=1)
    max_runtime_minutes: int | None = Field(default=None, ge=1)
    max_memory_mb: int | None = Field(default=None, ge=256)
    max_cpu: int | None = Field(default=None, ge=1)
    allow_csv_submissions: bool | None = None
    allow_notebook_submissions: bool | None = None
    source_retention_days: int | None = Field(default=None, ge=1)
    log_retention_days: int | None = Field(default=None, ge=1)
    artifact_retention_days: int | None = Field(default=None, ge=1)
    private_leaderboard_opens_at: datetime | None = None
    phase: CompetitionPhaseCreateRequest | None = None


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
    submission_mode: str
    scoring_metric: str
    scoring_direction: str
    best_submission_rule: str
    max_submissions_per_day: int
    max_runtime_minutes: int
    max_memory_mb: int
    max_cpu: int
    allow_csv_submissions: bool
    allow_notebook_submissions: bool
    source_retention_days: int
    log_retention_days: int
    artifact_retention_days: int
    private_leaderboard_opens_at: datetime | None
    solution_filename: str | None
    test_filename: str | None
    metric_script_filename: str | None
    phases: list[CompetitionPhaseResponse]
