"""public private scores and late submissions"""

import sqlalchemy as sa
from alembic import op

revision = "0007_split_scores_late"
down_revision = "0006_worker_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "submissions",
        sa.Column("is_late_submission", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "scores",
        sa.Column("public_score_value", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "scores",
        sa.Column("private_score_value", sa.Float(), nullable=False, server_default="0"),
    )
    op.execute(
        "UPDATE scores " "SET public_score_value = score_value, private_score_value = score_value"
    )


def downgrade() -> None:
    op.drop_column("scores", "private_score_value")
    op.drop_column("scores", "public_score_value")
    op.drop_column("submissions", "is_late_submission")
