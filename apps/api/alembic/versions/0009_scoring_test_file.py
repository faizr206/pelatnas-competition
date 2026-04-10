"""add scoring test file"""

import sqlalchemy as sa
from alembic import op

revision = "0009_scoring_test_file"
down_revision = "0008_worker_gpu_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "competitions",
        sa.Column("test_path", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "competitions",
        sa.Column("test_filename", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("competitions", "test_filename")
    op.drop_column("competitions", "test_path")
