"""add private leaderboard unlock timestamp"""

import sqlalchemy as sa
from alembic import op

revision = "0010_private_lb_unlock"
down_revision = "0009_scoring_test_file"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "competitions",
        sa.Column("private_leaderboard_opens_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("competitions", "private_leaderboard_opens_at")
