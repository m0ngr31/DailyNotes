"""Add kanban_enabled and kanban_columns to User model

Revision ID: 52e14ce1cf76
Revises: external_calendars_001
Create Date: 2025-12-11 12:12:01.152124

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "52e14ce1cf76"
down_revision = "external_calendars_001"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("kanban_enabled", sa.Boolean(), nullable=True))
        batch_op.add_column(
            sa.Column("kanban_columns", sa.String(length=512), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("kanban_columns")
        batch_op.drop_column("kanban_enabled")
