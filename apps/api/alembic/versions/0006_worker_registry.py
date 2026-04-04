"""worker registry"""

import sqlalchemy as sa
from alembic import op

revision = "0006_worker_registry"
down_revision = "0005_submission_mode"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "worker_nodes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("worker_id", sa.String(length=255), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("worker_id"),
    )
    op.create_index(op.f("ix_worker_nodes_worker_id"), "worker_nodes", ["worker_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_worker_nodes_worker_id"), table_name="worker_nodes")
    op.drop_table("worker_nodes")
