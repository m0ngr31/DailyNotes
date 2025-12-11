"""Add named unique constraint name for note title

Revision ID: c440f31aff28
Revises: 7bd1ee1840ca
Create Date: 2021-02-27 08:59:27.748780

"""

from alembic import op
import sqlalchemy as sa
import app.model_types


# revision identifiers, used by Alembic.
revision = "c440f31aff28"
down_revision = "7bd1ee1840ca"
branch_labels = None
depends_on = None


def upgrade():
    # Skip unique constraint on MySQL - BLOB columns can't have unique constraints without key length
    # This constraint is also not really needed since titles are encrypted and lookups use different logic
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        with op.batch_alter_table("note", schema=None) as batch_op:
            batch_op.create_unique_constraint("title_uniq", ["title"])


def downgrade():
    with op.batch_alter_table("note", schema=None) as batch_op:
        pass
