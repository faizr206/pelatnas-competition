"""phase 0 baseline"""

import sqlalchemy as sa
from alembic import op

revision = "0001_phase0_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "competitions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("slug", sa.String(length=255), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "competition_phases",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "competition_id",
            sa.String(length=36),
            sa.ForeignKey("competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submission_limit_per_day", sa.Integer(), nullable=False),
        sa.Column("scoring_version", sa.String(length=50), nullable=False),
        sa.Column("rules_version", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_competition_phases_competition_id",
        "competition_phases",
        ["competition_id"],
    )
    op.create_table(
        "submissions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "competition_id",
            sa.String(length=36),
            sa.ForeignKey("competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "phase_id",
            sa.String(length=36),
            sa.ForeignKey("competition_phases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("submission_type", sa.String(length=50), nullable=False),
        sa.Column("source_archive_path", sa.String(length=1024), nullable=False),
        sa.Column("manifest_path", sa.String(length=1024), nullable=False),
        sa.Column("runtime_image", sa.String(length=255), nullable=True),
        sa.Column("runtime_image_digest", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_submissions_competition_id", "submissions", ["competition_id"])
    op.create_index("ix_submissions_phase_id", "submissions", ["phase_id"])
    op.create_index("ix_submissions_user_id", "submissions", ["user_id"])
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "submission_id",
            sa.String(length=36),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("worker_id", sa.String(length=255), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_table(
        "submission_artifacts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "submission_id",
            sa.String(length=36),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("artifact_type", sa.String(length=100), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("checksum", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_submission_artifacts_submission_id", "submission_artifacts", ["submission_id"]
    )
    op.create_table(
        "scores",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "submission_id",
            sa.String(length=36),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("score_value", sa.Float(), nullable=False),
        sa.Column("scoring_version", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scores_submission_id", "scores", ["submission_id"])
    op.create_table(
        "leaderboard_entries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "competition_id",
            sa.String(length=36),
            sa.ForeignKey("competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "phase_id",
            sa.String(length=36),
            sa.ForeignKey("competition_phases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "best_submission_id",
            sa.String(length=36),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score_value", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("visibility_type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_leaderboard_entries_competition_id",
        "leaderboard_entries",
        ["competition_id"],
    )
    op.create_index("ix_leaderboard_entries_phase_id", "leaderboard_entries", ["phase_id"])
    op.create_index("ix_leaderboard_entries_user_id", "leaderboard_entries", ["user_id"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("actor_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_index("ix_leaderboard_entries_user_id", table_name="leaderboard_entries")
    op.drop_index("ix_leaderboard_entries_phase_id", table_name="leaderboard_entries")
    op.drop_index("ix_leaderboard_entries_competition_id", table_name="leaderboard_entries")
    op.drop_table("leaderboard_entries")
    op.drop_index("ix_scores_submission_id", table_name="scores")
    op.drop_table("scores")
    op.drop_index("ix_submission_artifacts_submission_id", table_name="submission_artifacts")
    op.drop_table("submission_artifacts")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_submissions_user_id", table_name="submissions")
    op.drop_index("ix_submissions_phase_id", table_name="submissions")
    op.drop_index("ix_submissions_competition_id", table_name="submissions")
    op.drop_table("submissions")
    op.drop_index("ix_competition_phases_competition_id", table_name="competition_phases")
    op.drop_table("competition_phases")
    op.drop_table("competitions")
    op.drop_table("users")
