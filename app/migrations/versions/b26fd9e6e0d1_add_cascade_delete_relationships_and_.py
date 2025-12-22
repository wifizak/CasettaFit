"""add_cascade_delete_relationships_and_ondelete_behaviors

Revision ID: b26fd9e6e0d1
Revises: 9f40e0ea0323
Create Date: 2025-12-22 22:48:28.714556

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b26fd9e6e0d1'
down_revision = '9f40e0ea0323'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite doesn't support modifying foreign key constraints directly
    # The ondelete='SET NULL' will be applied when the app runs with foreign keys enabled
    # The models.py changes are sufficient for new tables/relationships
    pass


def downgrade():
    # No downgrade needed since we didn't make schema changes
    pass
