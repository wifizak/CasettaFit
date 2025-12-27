from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import ProgramInstance, WorkoutSession, WorkoutSet, MasterExercise
from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload, selectinload

bp = Blueprint('history', __name__, url_prefix='/history')


@bp.route('/')
@login_required
def index():
    """History page with tabs for programs and exercises"""
    return render_template('history/index.html')


@bp.route('/api/programs')
@login_required
def get_program_history():
    """Get list of all program instances with completion stats - Optimized with eager loading"""
    instances = ProgramInstance.query.filter_by(
        user_id=current_user.id
    ).options(
        joinedload(ProgramInstance.program),
        joinedload(ProgramInstance.gym),
        selectinload(ProgramInstance.scheduled_days)
    ).order_by(desc(ProgramInstance.scheduled_date)).all()
    
    result = []
    for instance in instances:
        # Count total days and completed days
        total_days = len(instance.scheduled_days)
        completed_days = sum(1 for sd in instance.scheduled_days if sd.is_completed)
        
        # Get date range
        dates = [sd.calendar_date for sd in instance.scheduled_days]
        start_date = min(dates) if dates else instance.scheduled_date
        end_date = max(dates) if dates else None
        
        result.append({
            'id': instance.id,
            'program_name': instance.program.name,
            'gym_name': instance.gym.name if instance.gym else None,
            'scheduled_date': instance.scheduled_date.strftime('%Y-%m-%d'),
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
            'total_days': total_days,
            'completed_days': completed_days,
            'completion_percentage': round((completed_days / total_days * 100) if total_days > 0 else 0, 1)
        })
    
    return jsonify(result)


@bp.route('/api/exercises')
@login_required
def get_exercise_history():
    """Get list of all exercises performed with stats - Already optimized with aggregation"""
    # Get all exercises the user has logged
    exercise_stats = db.session.query(
        WorkoutSet.exercise_id,
        func.count(func.distinct(WorkoutSet.workout_session_id)).label('session_count'),
        func.count(WorkoutSet.id).label('total_sets'),
        func.max(WorkoutSet.weight).label('max_weight'),
        func.max(WorkoutSet.created_at).label('last_performed')
    ).join(WorkoutSet.workout_session).filter(
        WorkoutSet.workout_session.has(user_id=current_user.id)
    ).group_by(WorkoutSet.exercise_id).all()
    
    result = []
    for stat in exercise_stats:
        exercise = db.session.get(MasterExercise, stat.exercise_id)
        if exercise:
            result.append({
                'id': exercise.id,
                'name': exercise.name,
                'category': exercise.category,
                'primary_muscle': exercise.primary_muscle,
                'session_count': stat.session_count,
                'total_sets': stat.total_sets,
                'max_weight': stat.max_weight,
                'last_performed': stat.last_performed.strftime('%Y-%m-%d')
            })
    
    # Sort by last performed date, most recent first
    result.sort(key=lambda x: x['last_performed'], reverse=True)
    
    return jsonify(result)
