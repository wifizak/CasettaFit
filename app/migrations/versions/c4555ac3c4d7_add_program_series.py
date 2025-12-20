"""add_program_series

Revision ID: c4555ac3c4d7
Revises: d047dc846d81
Create Date: 2025-12-20 03:59:27.606638

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4555ac3c4d7'
down_revision = 'd047dc846d81'
branch_labels = None
depends_on = None


def upgrade():
    # Create program_series table
    op.create_table(
        'program_series',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('day_id', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('series_type', sa.String(20), nullable=False, server_default='single'),
        sa.Column('time_seconds', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['day_id'], ['program_days.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add new columns to program_exercises
    with op.batch_alter_table('program_exercises', schema=None) as batch_op:
        batch_op.add_column(sa.Column('series_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('superset_position', sa.Integer(), nullable=False, server_default='1'))
    
    # Migrate existing program_exercises to use series
    conn = op.get_bind()
    
    # Get all existing program exercises grouped by day
    result = conn.execute(sa.text("""
        SELECT DISTINCT day_id FROM program_exercises ORDER BY day_id
    """))
    
    day_ids = [row[0] for row in result]
    
    for day_id in day_ids:
        # Get exercises for this day ordered by order_index
        exercises = conn.execute(sa.text("""
            SELECT id, order_index FROM program_exercises 
            WHERE day_id = :day_id ORDER BY order_index
        """), {'day_id': day_id}).fetchall()
        
        for idx, ex_row in enumerate(exercises):
            # Create a series for each exercise
            conn.execute(sa.text("""
                INSERT INTO program_series (day_id, order_index, series_type)
                VALUES (:day_id, :order_index, 'single')
            """), {'day_id': day_id, 'order_index': idx})
            
            # Get the last inserted series_id
            series_id_result = conn.execute(sa.text("SELECT last_insert_rowid()"))
            series_id = series_id_result.scalar()
            
            # Update the exercise to reference the series
            conn.execute(sa.text("""
                UPDATE program_exercises 
                SET series_id = :series_id
                WHERE id = :ex_id
            """), {'series_id': series_id, 'ex_id': ex_row[0]})
    
    # Drop old columns using batch mode
    with op.batch_alter_table('program_exercises', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_program_exercises_series', 'program_series', ['series_id'], ['id'])
        batch_op.drop_column('day_id')
        batch_op.drop_column('order_index')


def downgrade():
    # Add back old columns
    op.add_column('program_exercises', sa.Column('day_id', sa.Integer(), nullable=True))
    op.add_column('program_exercises', sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'))
    
    # Migrate data back
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE program_exercises 
        SET day_id = (SELECT day_id FROM program_series WHERE program_series.id = program_exercises.series_id),
            order_index = (SELECT order_index FROM program_series WHERE program_series.id = program_exercises.series_id)
    """))
    
    # Create foreign key
    op.create_foreign_key(None, 'program_exercises', 'program_days', ['day_id'], ['id'])
    
    # Make day_id NOT NULL
    op.alter_column('program_exercises', 'day_id', nullable=False)
    
    # Drop new columns
    op.drop_constraint(None, 'program_exercises', type_='foreignkey')
    op.drop_column('program_exercises', 'superset_position')
    op.drop_column('program_exercises', 'series_id')
    
    # Drop series table
    op.drop_table('program_series')
