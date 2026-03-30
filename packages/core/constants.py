from enum import StrEnum


class JobStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COLLECTING = "collecting"
    SCORING = "scoring"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class SubmissionStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COLLECTING = "collecting"
    SCORING = "scoring"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class SubmissionType(StrEnum):
    CSV = "csv"
    NOTEBOOK = "notebook"


class ScoringDirection(StrEnum):
    MAX = "max"
    MIN = "min"
