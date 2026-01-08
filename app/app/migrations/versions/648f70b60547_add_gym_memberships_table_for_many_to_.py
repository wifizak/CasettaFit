"""Add gym_memberships table for many-to-many user-gym relationship

Revision ID: 648f70b60547
Revises: 303d78475b9f
Create Date: 2026-01-08 12:40:07.631859

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '648f70b60547'
down_revision = '303d78475b9f'
branch_labels = None
depends_on = None


def upgrade():
    # Create gym_memberships table
    op.create_table('gym_memberships',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('gym_id', sa.Integer(), nullable=False),
    sa.Column('joined_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['gym_id'], ['user_gyms.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'gym_id', name='unique_user_gym_membership')
    )


def downgrade():
    # Drop gym_memberships table
    op.drop_table('gym_memberships')

