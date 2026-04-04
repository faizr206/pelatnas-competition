from pydantic import BaseModel


class MetricTemplateResponse(BaseModel):
    name: str
    title: str
    description: str
    code: str
    default_metric_name: str
    default_scoring_direction: str


class ScoringConfigResponse(BaseModel):
    competition_id: str
    submission_mode: str
    scoring_metric: str
    scoring_direction: str
    solution_filename: str | None
    metric_script_filename: str | None
    metric_code: str | None
    templates: list[MetricTemplateResponse]


class RescoreSubmissionsResponse(BaseModel):
    queued_submission_count: int
    job_ids: list[str]
