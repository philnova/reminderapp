"""create user table

Revision ID: 2df2a2cb6d38
Revises: 523a3ccae42a
Create Date: 2016-03-16 15:01:43.075645

"""

# revision identifiers, used by Alembic.
revision = '2df2a2cb6d38'
down_revision = '523a3ccae42a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('google_id', sa.String(200)),
        sa.Column('picture', sa.String(200)),
        sa.Column('email', sa.String(200)),
        sa.Column('phone',sa.String(200)))


def downgrade():
    op.drop_table('users')
