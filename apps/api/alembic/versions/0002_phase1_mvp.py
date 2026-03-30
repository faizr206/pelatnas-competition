"""phase 1 mvp"""

import sqlalchemy as sa
from alembic import op

revision = "0002_phase1_mvp"
down_revision = "0001_phase0_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "competitions",
        sa.Column(
            "scoring_metric",
            sa.String(length=100),
            nullable=False,
            server_default="row_count",
        ),
    )
    op.add_column(
        "competitions",
        sa.Column(
            "scoring_direction",
            sa.String(length=20),
            nullable=False,
            server_default="max",
        ),
    )
    op.add_column(
        "competitions",
        sa.Column(
            "best_submission_rule",
            sa.String(length=50),
            nullable=False,
            server_default="best_score",
        ),
    )
    op.add_column(
        "competitions",
        sa.Column("max_submissions_per_day", sa.Integer(), nullable=False, server_default="5"),
    )
    op.add_column(
        "competitions",
        sa.Column("max_runtime_minutes", sa.Integer(), nullable=False, server_default="20"),
    )
    op.add_column(
        "competitions",
        sa.Column("max_memory_mb", sa.Integer(), nullable=False, server_default="4096"),
    )
    op.add_column(
        "competitions",
        sa.Column("max_cpu", sa.Integer(), nullable=False, server_default="2"),
    )
    op.add_column(
        "competitions",
        sa.Column("allow_csv_submissions", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "competitions",
        sa.Column(
            "allow_notebook_submissions", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    op.add_column(
        "competitions",
        sa.Column("source_retention_days", sa.Integer(), nullable=False, server_default="30"),
    )
    op.add_column(
        "competitions",
        sa.Column("log_retention_days", sa.Integer(), nullable=False, server_default="14"),
    )
    op.add_column(
        "competitions",
        sa.Column("artifact_retention_days", sa.Integer(), nullable=False, server_default="14"),
    )

    op.create_table(
        "datasets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "competition_id",
            sa.String(length=36),
            sa.ForeignKey("competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("checksum", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_datasets_competition_id", "datasets", ["competition_id"])

    with op.batch_alter_table("submissions") as batch_op:
        batch_op.alter_column(
            "manifest_path",
            existing_type=sa.String(length=1024),
            nullable=True,
        )
        batch_op.add_column(
            sa.Column(
                "source_original_filename",
                sa.String(length=255),
                nullable=False,
                server_default="",
            )
        )
        batch_op.add_column(
            sa.Column(
                "source_content_type",
                sa.String(length=255),
                nullable=False,
                server_default="",
            )
        )
        batch_op.add_column(
            sa.Column("source_checksum", sa.String(length=255), nullable=False, server_default="")
        )
        batch_op.add_column(
            sa.Column("source_size_bytes", sa.BigInteger(), nullable=False, server_default="0")
        )


def downgrade() -> None:
    with op.batch_alter_table("submissions") as batch_op:
        batch_op.drop_column("source_size_bytes")
        batch_op.drop_column("source_checksum")
        batch_op.drop_column("source_content_type")
        batch_op.drop_column("source_original_filename")
        batch_op.alter_column(
            "manifest_path",
            existing_type=sa.String(length=1024),
            nullable=False,
        )

    op.drop_index("ix_datasets_competition_id", table_name="datasets")
    op.drop_table("datasets")

    op.drop_column("competitions", "artifact_retention_days")
    op.drop_column("competitions", "log_retention_days")
    op.drop_column("competitions", "source_retention_days")
    op.drop_column("competitions", "allow_notebook_submissions")
    op.drop_column("competitions", "allow_csv_submissions")
    op.drop_column("competitions", "max_cpu")
    op.drop_column("competitions", "max_memory_mb")
    op.drop_column("competitions", "max_runtime_minutes")
    op.drop_column("competitions", "max_submissions_per_day")
    op.drop_column("competitions", "best_submission_rule")
    op.drop_column("competitions", "scoring_direction")
    op.drop_column("competitions", "scoring_metric")
