"""add user leaderboard hide flag"""

import sqlalchemy as sa
from alembic import op

revision = "0011_user_lb_hide"
down_revision = "0010_private_lb_unlock"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "hide_from_leaderboard",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "hide_from_leaderboard")
