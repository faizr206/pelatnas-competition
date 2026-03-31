"""competition scoring config"""

import sqlalchemy as sa
from alembic import op

revision = "0003_scoring_config"
down_revision = "0002_phase1_mvp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "competitions",
        sa.Column("solution_path", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "competitions",
        sa.Column("solution_filename", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "competitions",
        sa.Column("metric_script_path", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "competitions",
        sa.Column("metric_script_filename", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("competitions", "metric_script_filename")
    op.drop_column("competitions", "metric_script_path")
    op.drop_column("competitions", "solution_filename")
    op.drop_column("competitions", "solution_path")
