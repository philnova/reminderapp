"""Add a column

Revision ID: 523a3ccae42a
Revises: 3e7ebdde2eb
Create Date: 2016-03-15 17:09:04.953366

"""

# revision identifiers, used by Alembic.
revision = '523a3ccae42a'
down_revision = '3e7ebdde2eb'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('appointments', sa.Column('reminder', sa.String(255), nullable=False))


def downgrade():
    op.drop_column('appointments', 'reminder')
