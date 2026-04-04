"""worker gpu status"""

import sqlalchemy as sa
from alembic import op

revision = "0008_worker_gpu_status"
down_revision = "0007_split_scores_late"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "worker_nodes",
        sa.Column("gpu_available", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("worker_nodes", "gpu_available", server_default=None)


def downgrade() -> None:
    op.drop_column("worker_nodes", "gpu_available")
