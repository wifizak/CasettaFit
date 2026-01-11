from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import (
    WorkoutSession, WorkoutSet, ScheduledDay, MasterExercise,
    ProgramExercise, InstanceExerciseWeight, ProgramDay, ProgramSeries, ProgramInstance
)
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime
import json

bp = Blueprint('workout', __name__, url_prefix='/workout')


@bp.route('/start/<int:scheduled_day_id>')
@login_required
def start_workout(scheduled_day_id):
    """Start a workout from a scheduled day"""
    scheduled_day = ScheduledDay.query.filter_by(
        id=scheduled_day_id,
        user_id=current_user.id
    ).options(
        joinedload(ScheduledDay.gym)
    ).first_or_404()
    
    # Check if there's already an active session for this scheduled day
    active_session = WorkoutSession.query.filter_by(
        scheduled_day_id=scheduled_day_id,
        user_id=current_user.id,
        is_completed=False
    ).first()
    
    if active_session:
        # Resume existing session
        return redirect(url_for('workout.execute_workout', session_id=active_session.id))
    
    # Create new workout session
    session = WorkoutSession(
        user_id=current_user.id,
        scheduled_day_id=scheduled_day_id,
        gym_id=scheduled_day.gym_id,
        started_at=datetime.utcnow()
    )
    db.session.add(session)
    db.session.commit()
    
    return redirect(url_for('workout.execute_workout', session_id=session.id))


@bp.route('/start-standalone')
@login_required
def start_standalone():
    """Start a standalone workout (not tied to a program)"""
    # Create new workout session without scheduled_day_id
    session = WorkoutSession(
        user_id=current_user.id,
        started_at=datetime.utcnow()
    )
    db.session.add(session)
    db.session.commit()
    
    return redirect(url_for('workout.execute_workout', session_id=session.id))


@bp.route('/execute/<int:session_id>')
@login_required
def execute_workout(session_id):
    """Main workout execution page - Optimized with eager loading"""
    session = WorkoutSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).options(
        joinedload(WorkoutSession.gym),
        joinedload(WorkoutSession.scheduled_day).joinedload(ScheduledDay.program),
        joinedload(WorkoutSession.scheduled_day).joinedload(ScheduledDay.program_day)
            .selectinload(ProgramDay.series)
            .selectinload(ProgramSeries.exercises)
            .joinedload(ProgramExercise.exercise)
    ).first_or_404()
    
    # Get workout structure if this is a scheduled workout
    workout_structure = None
    if session.scheduled_day:
        workout_structure = _get_workout_structure(session.scheduled_day)
    
    return render_template('workout/execute.html',
                         session=session,
                         workout_structure=workout_structure)


@bp.route('/api/session/<int:session_id>/data')
@login_required
def get_session_data(session_id):
    """Get full workout data including structure and logged sets - Optimized"""
    session = WorkoutSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).options(
        joinedload(WorkoutSession.gym),
        joinedload(WorkoutSession.scheduled_day).joinedload(ScheduledDay.program),
        joinedload(WorkoutSession.scheduled_day).joinedload(ScheduledDay.program_day)
            .selectinload(ProgramDay.series)
            .selectinload(ProgramSeries.exercises)
            .joinedload(ProgramExercise.exercise),
        joinedload(WorkoutSession.scheduled_day).joinedload(ScheduledDay.instance)
            .selectinload(ProgramInstance.custom_weights)
    ).first_or_404()
    
    data = {
        'session_id': session.id,
        'started_at': session.started_at.isoformat(),
        'is_completed': session.is_completed,
        'gym_name': session.gym.name if session.gym else None,
        'is_standalone': session.scheduled_day_id is None
    }
    
    # If this is a scheduled workout, include the program structure
    if session.scheduled_day:
        scheduled_day = session.scheduled_day
        data['program_name'] = scheduled_day.program.name
        data['day_name'] = scheduled_day.program_day.day_name or f'Day {scheduled_day.program_day.day_number}'
        data['calendar_date'] = scheduled_day.calendar_date.strftime('%Y-%m-%d')
        
        # Get custom weights for this instance
        custom_weights_map = {}
        if scheduled_day.instance:
            for cw in scheduled_day.instance.custom_weights:
                custom_weights_map[cw.program_exercise_id] = {
                    'weights': json.loads(cw.custom_weights) if cw.custom_weights else [],
                    'notes': cw.notes
                }
        
        # Build workout structure
        series_data = []
        for series in scheduled_day.program_day.series:
            exercises_data = []
            for prog_ex in series.exercises:
                # Get default weights
                default_weights = []
                if prog_ex.starting_weights:
                    try:
                        default_weights = json.loads(prog_ex.starting_weights)
                    except (json.JSONDecodeError, ValueError, TypeError):
                        # If JSON is invalid, use empty list
                        default_weights = []
                
                # Get custom weights if they exist
                suggested_weights = default_weights
                if prog_ex.id in custom_weights_map and custom_weights_map[prog_ex.id]['weights']:
                    suggested_weights = custom_weights_map[prog_ex.id]['weights']
                
                # Get previous workout history for this exercise
                previous_sets = _get_previous_sets(current_user.id, prog_ex.exercise_id)
                
                exercises_data.append({
                    'exercise_id': prog_ex.exercise_id,
                    'exercise_name': prog_ex.exercise.name,
                    'sets': prog_ex.sets,
                    'reps': prog_ex.reps,
                    'suggested_weights': suggested_weights,
                    'rest_time_seconds': prog_ex.rest_time_seconds,
                    'previous_sets': previous_sets
                })
            
            series_data.append({
                'series_type': series.series_type,
                'exercises': exercises_data,
                'time_seconds': series.time_seconds,
                'notes': series.notes
            })
        
        data['series'] = series_data
    
    # Get logged sets for this session
    logged_sets = {}
    for workout_set in session.sets.all():
        if workout_set.exercise_id not in logged_sets:
            logged_sets[workout_set.exercise_id] = []
        logged_sets[workout_set.exercise_id].append({
            'id': workout_set.id,
            'set_number': workout_set.set_number,
            'reps': workout_set.reps,
            'weight': workout_set.weight,
            'rpe': workout_set.rpe,
            'overall_rpe': workout_set.overall_rpe,
            'notes': workout_set.notes,
            'completed_at': workout_set.completed_at.isoformat()
        })
    
    data['logged_sets'] = logged_sets
    
    return jsonify(data)


@bp.route('/api/session/<int:session_id>/log-set', methods=['POST'])
@login_required
def log_set(session_id):
    """Log a set during workout"""
    session = WorkoutSession.query.filter_by(
        id=session_id,
        user_id=current_user.id,
        is_completed=False  # Prevent logging to completed sessions
    ).first_or_404()
    
    data = request.json
    exercise_id = data.get('exercise_id')
    set_number = data.get('set_number')
    reps = data.get('reps')
    weight = data.get('weight')
    rpe = data.get('rpe')
    notes = data.get('notes', '')
    
    if not exercise_id or not set_number:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Validate set_number is positive
    if set_number < 1:
        return jsonify({'success': False, 'error': 'Invalid set number'}), 400
    
    # Check if this set already exists (update case)
    existing_set = WorkoutSet.query.filter_by(
        workout_session_id=session_id,
        exercise_id=exercise_id,
        set_number=set_number
    ).first()
    
    if existing_set:
        # Update existing set
        existing_set.reps = reps
        existing_set.weight = weight
        existing_set.rpe = rpe
        existing_set.notes = notes
        existing_set.completed_at = datetime.utcnow()
        workout_set = existing_set
    else:
        # Create new set
        workout_set = WorkoutSet(
            workout_session_id=session_id,
            exercise_id=exercise_id,
            set_number=set_number,
            reps=reps,
            weight=weight,
            rpe=rpe,
            notes=notes,
            completed_at=datetime.utcnow()
        )
        db.session.add(workout_set)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'set_id': workout_set.id,
        'set_number': workout_set.set_number,
        'reps': workout_set.reps,
        'weight': workout_set.weight,
        'rpe': workout_set.rpe
    })


@bp.route('/api/session/<int:session_id>/overall-rpe', methods=['POST'])
@login_required
def save_overall_rpe(session_id):
    """Save overall RPE for an exercise in this session"""
    session = WorkoutSession.query.filter_by(
        id=session_id,
        user_id=current_user.id,
        is_completed=False  # Prevent updating completed sessions
    ).first_or_404()
    
    data = request.json
    exercise_id = data.get('exercise_id')
    overall_rpe = data.get('overall_rpe')
    
    if not exercise_id or not overall_rpe:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Validate RPE value
    if overall_rpe not in ['-', '=', '+']:
        return jsonify({'success': False, 'error': 'Invalid RPE value'}), 400
    
    # Update all sets of this exercise with overall_rpe
    # This ensures the overall RPE is stored consistently across all sets
    updated_count = WorkoutSet.query.filter_by(
        workout_session_id=session_id,
        exercise_id=exercise_id
    ).update({'overall_rpe': overall_rpe})
    
    if updated_count == 0:
        return jsonify({'success': False, 'error': 'No sets logged for this exercise yet'}), 400
    
    db.session.commit()
    
    return jsonify({'success': True, 'overall_rpe': overall_rpe})


@bp.route('/api/session/<int:session_id>/complete', methods=['POST'])
@login_required
def complete_workout(session_id):
    """Mark workout session as complete"""
    session = WorkoutSession.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.json
    notes = data.get('notes', '')
    
    session.is_completed = True
    session.completed_at = datetime.utcnow()
    session.notes = notes
    
    # Mark scheduled day as completed if this was a scheduled workout
    if session.scheduled_day:
        session.scheduled_day.is_completed = True
    
    db.session.commit()
    
    return jsonify({'success': True, 'completed_at': session.completed_at.isoformat()})


@bp.route('/api/exercises/search')
@login_required
def search_exercises():
    """Search exercises for standalone workout logging"""
    query = request.args.get('q', '').strip()
    
    if not query:
        # Return recent exercises
        recent_exercises = db.session.query(MasterExercise)\
            .join(WorkoutSet, WorkoutSet.exercise_id == MasterExercise.id)\
            .join(WorkoutSession, WorkoutSession.id == WorkoutSet.workout_session_id)\
            .filter(WorkoutSession.user_id == current_user.id)\
            .group_by(MasterExercise.id)\
            .order_by(db.func.max(WorkoutSet.completed_at).desc())\
            .limit(10)\
            .all()
        
        exercises = [{'id': ex.id, 'name': ex.name, 'category': ex.category} for ex in recent_exercises]
    else:
        # Search by name
        exercises_query = MasterExercise.query.filter(
            MasterExercise.name.ilike(f'%{query}%')
        ).limit(20).all()
        
        exercises = [{'id': ex.id, 'name': ex.name, 'category': ex.category} for ex in exercises_query]
    
    return jsonify({'exercises': exercises})


def _get_workout_structure(scheduled_day):
    """Helper to build workout structure from scheduled day"""
    structure = {
        'program_name': scheduled_day.program.name,
        'day_name': scheduled_day.program_day.day_name,
        'series': []
    }
    
    for series in scheduled_day.program_day.series:
        series_data = {
            'type': series.series_type,
            'exercises': []
        }
        
        for prog_ex in series.exercises:
            series_data['exercises'].append({
                'exercise_id': prog_ex.exercise_id,
                'name': prog_ex.exercise.name,
                'sets': prog_ex.sets,
                'reps': prog_ex.reps
            })
        
        structure['series'].append(series_data)
    
    return structure


def _get_previous_sets(user_id, exercise_id, limit=5):
    """Get previous workout sets for an exercise"""
    previous_sets = WorkoutSet.query\
        .join(WorkoutSession)\
        .filter(
            WorkoutSession.user_id == user_id,
            WorkoutSet.exercise_id == exercise_id,
            WorkoutSession.is_completed == True
        )\
        .order_by(WorkoutSet.completed_at.desc())\
        .limit(limit)\
        .all()
    
    return [{
        'date': s.completed_at.strftime('%Y-%m-%d'),
        'reps': s.reps,
        'weight': s.weight,
        'rpe': s.rpe
    } for s in previous_sets]
