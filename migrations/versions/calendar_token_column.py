"""Add calendar_token column to User table

Revision ID: calendar_token_001
Revises: vim_mode_001
Create Date: 2025-02-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'calendar_token_001'
down_revision = 'vim_mode_001'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('calendar_token', sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint('uq_user_calendar_token', ['calendar_token'])


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_calendar_token', type_='unique')
        batch_op.drop_column('calendar_token')
