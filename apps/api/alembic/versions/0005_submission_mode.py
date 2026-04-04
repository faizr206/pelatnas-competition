"""competition submission mode"""

import sqlalchemy as sa
from alembic import op

revision = "0005_submission_mode"
down_revision = "0004_user_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "competitions",
        sa.Column(
            "submission_mode",
            sa.String(length=50),
            nullable=False,
            server_default="prediction_file",
        ),
    )


def downgrade() -> None:
    op.drop_column("competitions", "submission_mode")
