"""create foreign key for appointments

Revision ID: 2017efcb843d
Revises: 2df2a2cb6d38
Create Date: 2016-03-16 15:38:42.381877

"""

# revision identifiers, used by Alembic.
revision = '2017efcb843d'
down_revision = '2df2a2cb6d38'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('appointments', sa.Column('user_id', sa.Integer()))
    op.create_foreign_key(
        'fk_appointments_users',
        'appointments', 'users',
        ['user_id'], ['id'])


def downgrade():
    op.drop_constraint('appointments', 'fk_appointments_users')
    op.drop_column('appointments', 'user_id')
