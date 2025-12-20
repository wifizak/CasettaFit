"""change_starting_weight_to_array

Revision ID: f29ea115180a
Revises: c558ea5d4ef4
Create Date: 2025-12-20 05:07:21.559232

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f29ea115180a'
down_revision = 'c558ea5d4ef4'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite doesn't support renaming columns directly, so we use batch mode
    with op.batch_alter_table('program_exercises', schema=None) as batch_op:
        # Add new column
        batch_op.add_column(sa.Column('starting_weights', sa.Text(), nullable=True))
        
        # Migrate data: convert single weight to JSON array
        # This will be done via SQL in a separate connection
        
        # Drop old column
        batch_op.drop_column('starting_weight')
    
    # Migrate existing data
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE program_exercises 
        SET starting_weights = '[]'
        WHERE starting_weights IS NULL
    """))


def downgrade():
    with op.batch_alter_table('program_exercises', schema=None) as batch_op:
        # Add back the old column
        batch_op.add_column(sa.Column('starting_weight', sa.Float(), nullable=True))
        
        # Drop new column
        batch_op.drop_column('starting_weights')
