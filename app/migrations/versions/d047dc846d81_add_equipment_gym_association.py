"""add_equipment_gym_association

Revision ID: d047dc846d81
Revises: 7c4b68c83475
Create Date: 2025-12-20 02:52:33.367513

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd047dc846d81'
down_revision = '7c4b68c83475'
branch_labels = None
depends_on = None


def upgrade():
    # Create association table for equipment-gym many-to-many relationship
    op.create_table(
        'equipment_gym_association',
        sa.Column('equipment_id', sa.Integer(), sa.ForeignKey('master_equipment.id'), primary_key=True),
        sa.Column('gym_id', sa.Integer(), sa.ForeignKey('user_gyms.id'), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
    )


def downgrade():
    op.drop_table('equipment_gym_association')
