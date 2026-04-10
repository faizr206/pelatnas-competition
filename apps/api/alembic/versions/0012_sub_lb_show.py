"""add submission leaderboard visibility flag"""

import sqlalchemy as sa
from alembic import op

revision = "0012_sub_lb_show"
down_revision = "0011_user_lb_hide"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "submissions",
        sa.Column(
            "display_on_leaderboard",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("submissions", "display_on_leaderboard")
