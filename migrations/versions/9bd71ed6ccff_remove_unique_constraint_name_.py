"""Remove unique constraint name for note title

Revision ID: 9bd71ed6ccff
Revises: c440f31aff28
Create Date: 2021-02-27 15:10:54.803203

"""

from alembic import op
import sqlalchemy as sa
import app.model_types


# revision identifiers, used by Alembic.
revision = "9bd71ed6ccff"
down_revision = "c440f31aff28"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("note", schema=None) as batch_op:
        batch_op.drop_constraint("title_uniq", type_="unique")


def downgrade():
    pass
