from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.core.time import utcnow
from packages.db.base import Base


def generate_id() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[Any] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[Any] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    password_changed_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Competition(TimestampMixin, Base):
    __tablename__ = "competitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(String(50), nullable=False, default="public")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    submission_mode: Mapped[str] = mapped_column(
        String(50), nullable=False, default="prediction_file"
    )
    scoring_metric: Mapped[str] = mapped_column(String(100), nullable=False, default="row_count")
    scoring_direction: Mapped[str] = mapped_column(String(20), nullable=False, default="max")
    best_submission_rule: Mapped[str] = mapped_column(
        String(50), nullable=False, default="best_score"
    )
    max_submissions_per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    max_runtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    max_memory_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=4096)
    max_cpu: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    allow_csv_submissions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allow_notebook_submissions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    log_retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    artifact_retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    solution_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    solution_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metric_script_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    metric_script_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phases: Mapped[list[CompetitionPhase]] = relationship(
        back_populates="competition", cascade="all, delete-orphan"
    )
    datasets: Mapped[list[Dataset]] = relationship(
        back_populates="competition", cascade="all, delete-orphan"
    )


class CompetitionPhase(TimestampMixin, Base):
    __tablename__ = "competition_phases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    competition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("competitions.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    starts_at: Mapped[Any] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[Any] = mapped_column(DateTime(timezone=True), nullable=False)
    submission_limit_per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    scoring_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1")
    rules_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1")
    competition: Mapped[Competition] = relationship(back_populates="phases")


class Dataset(TimestampMixin, Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    competition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("competitions.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    checksum: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    competition: Mapped[Competition] = relationship(back_populates="datasets")


class Submission(TimestampMixin, Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    competition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("competitions.id", ondelete="CASCADE"), index=True
    )
    phase_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("competition_phases.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    submission_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_archive_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    manifest_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    source_checksum: Mapped[str] = mapped_column(String(255), nullable=False)
    source_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    runtime_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    runtime_image_digest: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    submission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("submissions.id", ondelete="CASCADE")
    )
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    queued_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)


class SubmissionArtifact(TimestampMixin, Base):
    __tablename__ = "submission_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    submission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("submissions.id", ondelete="CASCADE"), index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)


class Score(TimestampMixin, Base):
    __tablename__ = "scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    submission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("submissions.id", ondelete="CASCADE"), index=True
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    score_value: Mapped[float] = mapped_column(Float, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(50), nullable=False)


class LeaderboardEntry(TimestampMixin, Base):
    __tablename__ = "leaderboard_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    competition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("competitions.id", ondelete="CASCADE"), index=True
    )
    phase_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("competition_phases.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    best_submission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("submissions.id", ondelete="CASCADE")
    )
    score_value: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    visibility_type: Mapped[str] = mapped_column(String(50), nullable=False)


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
