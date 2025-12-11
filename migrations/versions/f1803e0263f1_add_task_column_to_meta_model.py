"""Add task_column to Meta model

Revision ID: f1803e0263f1
Revises: 52e14ce1cf76
Create Date: 2025-12-11 12:17:03.648630

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1803e0263f1"
down_revision = "52e14ce1cf76"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("meta", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("task_column", sa.String(length=64), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("meta", schema=None) as batch_op:
        batch_op.drop_column("task_column")
