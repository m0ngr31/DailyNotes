"""Add external calendars table

Revision ID: external_calendars_001
Revises: calendar_token_001
Create Date: 2025-02-15 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
import app.model_types


# revision identifiers, used by Alembic.
revision = "external_calendars_001"
down_revision = "calendar_token_001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "external_calendar",
        sa.Column("uuid", app.model_types.GUID(), nullable=False),
        sa.Column("user_id", app.model_types.GUID(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("color", sa.String(length=16), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.uuid"],
        ),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_index(
        op.f("ix_external_calendar_uuid"), "external_calendar", ["uuid"], unique=True
    )


def downgrade():
    op.drop_index(op.f("ix_external_calendar_uuid"), table_name="external_calendar")
    op.drop_table("external_calendar")
