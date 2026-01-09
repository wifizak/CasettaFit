from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app import db
from app.models import Program, ProgramWeek, ProgramDay, ProgramSeries, ProgramExercise, ScheduledDay, ProgramInstance, InstanceExerciseWeight, WorkoutSession, WorkoutSet
from sqlalchemy.orm import joinedload
import json

bp = Blueprint('calendar', __name__, url_prefix='/calendar')


@bp.route('/')
@login_required
def index():
    """Main calendar view"""
    from app.models import UserGym, GymMembership
    from sqlalchemy import or_
    
    programs = Program.query.filter_by(created_by=current_user.id).order_by(Program.name).all()
    
    # Get gyms user owns or is a member of
    gyms = UserGym.query.filter(
        or_(
            UserGym.user_id == current_user.id,
            UserGym.id.in_(
                db.session.query(GymMembership.gym_id).filter_by(user_id=current_user.id)
            )
        )
    ).order_by(UserGym.name).all()
    
    instances = ProgramInstance.query.filter_by(user_id=current_user.id).order_by(ProgramInstance.scheduled_date.desc()).all()
    return render_template('calendar/index.html', programs=programs, gyms=gyms, instances=instances)


@bp.route('/events')
@login_required
def get_events():
    """Get all scheduled workouts as FullCalendar events - Optimized with eager loading"""
    scheduled_days = ScheduledDay.query.filter_by(
        user_id=current_user.id
    ).options(
        joinedload(ScheduledDay.program),
        joinedload(ScheduledDay.program_day),
        joinedload(ScheduledDay.gym)
    ).order_by(ScheduledDay.calendar_date).all()
    
    events = []
    for sd in scheduled_days:
        event_title = f"{sd.program.name} - {sd.program_day.day_name or 'Day ' + str(sd.program_day.day_number)}"
        
        events.append({
            'id': sd.id,
            'title': event_title,
            'start': sd.calendar_date.isoformat(),
            'allDay': True,
            'extendedProps': {
                'programId': sd.program_id,
                'programDayId': sd.program_day_id,
                'gymName': sd.gym.name if sd.gym else None,
                'isCompleted': sd.is_completed
            },
            'classNames': ['fc-event-completed'] if sd.is_completed else []
        })
    
    return jsonify(events)


@bp.route('/program/<int:program_id>/details')
@login_required
def program_details(program_id):
    """Get program structure for scheduling"""
    program = Program.query.filter_by(id=program_id, created_by=current_user.id).first_or_404()
    
    weeks_data = []
    for week in program.weeks:
        days_data = []
        for day in week.days:
            days_data.append({
                'id': day.id,
                'name': day.day_name or f'Day {day.day_number}',
                'day_number': day.day_number
            })
        weeks_data.append({
            'id': week.id,
            'week_number': week.week_number,
            'days': days_data
        })
    
    return jsonify({
        'id': program.id,
        'name': program.name,
        'weeks': weeks_data
    })


@bp.route('/schedule', methods=['POST'])
@login_required
def schedule_program():
    """Schedule a program with day mappings"""
    data = request.get_json()
    program_id = data.get('program_id')
    gym_id = data.get('gym_id')
    mappings = data.get('mappings', [])
    force = data.get('force', False)
    
    if not program_id or not mappings:
        return jsonify({'success': False, 'error': 'Missing required data'}), 400
    
    # Verify program belongs to user
    program = Program.query.filter_by(id=program_id, created_by=current_user.id).first()
    if not program:
        return jsonify({'success': False, 'error': 'Program not found'}), 404
    
    # Check for conflicts (same program, same date)
    conflicts = []
    if not force:
        for mapping in mappings:
            calendar_date = datetime.strptime(mapping['calendar_date'], '%Y-%m-%d').date()
            existing = ScheduledDay.query.filter_by(
                user_id=current_user.id,
                program_id=program_id,
                calendar_date=calendar_date
            ).first()
            
            if existing:
                program_day = ProgramDay.query.get(mapping['program_day_id'])
                conflicts.append({
                    'date': mapping['calendar_date'],
                    'existing_day': existing.program_day.day_name or f'Day {existing.program_day.day_number}',
                    'new_day': program_day.day_name or f'Day {program_day.day_number}' if program_day else 'Unknown'
                })
    
    if conflicts:
        return jsonify({
            'success': False,
            'conflicts': conflicts,
            'message': 'Some dates already have workouts from this program'
        })
    
    # Create program instance
    first_date = min(datetime.strptime(m['calendar_date'], '%Y-%m-%d').date() for m in mappings)
    instance = ProgramInstance(
        user_id=current_user.id,
        program_id=program_id,
        gym_id=gym_id if gym_id else None,
        scheduled_date=first_date
    )
    db.session.add(instance)
    db.session.flush()  # Get the instance ID
    
    # Create scheduled days
    for mapping in mappings:
        calendar_date = datetime.strptime(mapping['calendar_date'], '%Y-%m-%d').date()
        program_day_id = mapping['program_day_id']
        
        scheduled_day = ScheduledDay(
            user_id=current_user.id,
            program_id=program_id,
            program_day_id=program_day_id,
            instance_id=instance.id,
            gym_id=gym_id if gym_id else None,
            calendar_date=calendar_date
        )
        db.session.add(scheduled_day)
    
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/reschedule/<int:scheduled_day_id>', methods=['POST'])
@login_required
def reschedule_day(scheduled_day_id):
    """Reschedule a workout to a new date"""
    scheduled_day = ScheduledDay.query.filter_by(
        id=scheduled_day_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    new_date_str = data.get('new_date')
    action = data.get('action')  # 'swap' or 'shift' or None
    conflict_id = data.get('conflict_id')
    
    if not new_date_str:
        return jsonify({'success': False, 'error': 'Missing new date'}), 400
    
    new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
    old_date = scheduled_day.calendar_date
    
    # Check for conflicts (same program, same date, different scheduled_day)
    conflict = ScheduledDay.query.filter(
        ScheduledDay.user_id == current_user.id,
        ScheduledDay.program_id == scheduled_day.program_id,
        ScheduledDay.calendar_date == new_date,
        ScheduledDay.id != scheduled_day_id
    ).first()
    
    if conflict and not action:
        # There's a conflict and user hasn't chosen an action yet
        return jsonify({
            'success': False,
            'conflict': True,
            'conflict_details': {
                'conflict_id': conflict.id,
                'existing_day_name': conflict.program_day.day_name or f'Day {conflict.program_day.day_number}'
            }
        })
    
    if action == 'swap' and conflict_id:
        # Swap: Move the conflicting day to the old date
        conflict_day = ScheduledDay.query.filter_by(
            id=conflict_id,
            user_id=current_user.id
        ).first()
        
        if conflict_day:
            conflict_day.calendar_date = old_date
            scheduled_day.calendar_date = new_date
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Conflict day not found'}), 404
    
    elif action == 'shift' and conflict_id:
        # Shift: Move the conflicting day to the next available date
        conflict_day = ScheduledDay.query.filter_by(
            id=conflict_id,
            user_id=current_user.id
        ).first()
        
        if conflict_day:
            # Find next available date
            next_date = new_date + timedelta(days=1)
            max_attempts = 365  # Prevent infinite loop
            
            for _ in range(max_attempts):
                existing = ScheduledDay.query.filter(
                    ScheduledDay.user_id == current_user.id,
                    ScheduledDay.program_id == scheduled_day.program_id,
                    ScheduledDay.calendar_date == next_date
                ).first()
                
                if not existing:
                    # Found an available date
                    conflict_day.calendar_date = next_date
                    scheduled_day.calendar_date = new_date
                    db.session.commit()
                    return jsonify({
                        'success': True,
                        'shifted_to': next_date.strftime('%A, %B %d, %Y')
                    })
                
                next_date += timedelta(days=1)
            
            return jsonify({'success': False, 'error': 'Could not find available date'}), 500
        else:
            return jsonify({'success': False, 'error': 'Conflict day not found'}), 404
    
    # No conflict or no action needed
    scheduled_day.calendar_date = new_date
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/scheduled-day/<int:scheduled_day_id>')
@login_required
def get_scheduled_day(scheduled_day_id):
    """Get details of a scheduled day"""
    scheduled_day = ScheduledDay.query.filter_by(
        id=scheduled_day_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Get custom weights for this instance if it exists
    custom_weights_map = {}
    if scheduled_day.instance:
        for cw in scheduled_day.instance.custom_weights:
            custom_weights_map[cw.program_exercise_id] = {
                'weights': json.loads(cw.custom_weights) if cw.custom_weights else [],
                'notes': cw.notes
            }
    
    # Get series and exercises for this day
    series_data = []
    for series in scheduled_day.program_day.series:
        exercises_data = []
        for prog_ex in series.exercises:
            # Get default weights from program
            default_weights = []
            if prog_ex.starting_weights:
                try:
                    default_weights = json.loads(prog_ex.starting_weights)
                except (json.JSONDecodeError, ValueError, TypeError):
                    # If JSON is invalid, use empty list
                    default_weights = []
            
            # Get custom weights if they exist
            custom_weights = None
            custom_notes = None
            if prog_ex.id in custom_weights_map:
                custom_weights = custom_weights_map[prog_ex.id]['weights']
                custom_notes = custom_weights_map[prog_ex.id]['notes']
            
            exercises_data.append({
                'exercise_name': prog_ex.exercise.name,
                'sets': prog_ex.sets,
                'reps': prog_ex.reps,
                'default_weights': default_weights,
                'custom_weights': custom_weights,
                'custom_notes': custom_notes,
                'rest_time_seconds': prog_ex.rest_time_seconds
            })
        
        series_data.append({
            'series_type': series.series_type,
            'exercises': exercises_data,
            'time_seconds': series.time_seconds,
            'notes': series.notes
        })
    
    return jsonify({
        'id': scheduled_day.id,
        'program_name': scheduled_day.program.name,
        'day_name': scheduled_day.program_day.day_name or f'Day {scheduled_day.program_day.day_number}',
        'gym_name': scheduled_day.gym.name if scheduled_day.gym else None,
        'calendar_date': scheduled_day.calendar_date.strftime('%Y-%m-%d'),
        'is_completed': scheduled_day.is_completed,
        'instance_id': scheduled_day.instance_id,
        'series': series_data
    })


@bp.route('/scheduled-day/<int:scheduled_day_id>', methods=['DELETE'])
@login_required
def delete_scheduled_day(scheduled_day_id):
    """Delete a scheduled workout"""
    scheduled_day = ScheduledDay.query.filter_by(
        id=scheduled_day_id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(scheduled_day)
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/missing-days')
@login_required
def get_missing_days():
    """Get all program days that should be scheduled but aren't"""
    instances = ProgramInstance.query.filter_by(user_id=current_user.id).all()
    
    missing_days = []
    for instance in instances:
        # Get all days that are scheduled for this instance
        scheduled_day_ids = set(
            sd.program_day_id for sd in instance.scheduled_days
        )
        
        # Get all days that should exist in the program
        program = instance.program
        all_program_day_ids = set()
        for week in program.weeks:
            for day in week.days:
                all_program_day_ids.add(day.id)
        
        # Find missing days
        missing_day_ids = all_program_day_ids - scheduled_day_ids
        
        for day_id in missing_day_ids:
            day = ProgramDay.query.get(day_id)
            if day:
                missing_days.append({
                    'id': f'missing_{instance.id}_{day.id}',
                    'instance_id': instance.id,
                    'program_day_id': day.id,
                    'program_name': program.name,
                    'day_name': day.day_name or f'Day {day.day_number}',
                    'week_number': day.week.week_number,
                    'gym_name': instance.gym.name if instance.gym else None
                })
    
    return jsonify(missing_days)


@bp.route('/schedule-missing-day', methods=['POST'])
@login_required
def schedule_missing_day():
    """Schedule a missing day to a specific date"""
    data = request.get_json()
    instance_id = data.get('instance_id')
    program_day_id = data.get('program_day_id')
    calendar_date_str = data.get('calendar_date')
    
    if not all([instance_id, program_day_id, calendar_date_str]):
        return jsonify({'success': False, 'error': 'Missing required data'}), 400
    
    instance = ProgramInstance.query.filter_by(
        id=instance_id,
        user_id=current_user.id
    ).first_or_404()
    
    calendar_date = datetime.strptime(calendar_date_str, '%Y-%m-%d').date()
    
    # Check for conflicts
    conflict = ScheduledDay.query.filter(
        ScheduledDay.user_id == current_user.id,
        ScheduledDay.program_id == instance.program_id,
        ScheduledDay.calendar_date == calendar_date,
        ScheduledDay.instance_id == instance_id
    ).first()
    
    if conflict:
        return jsonify({
            'success': False,
            'conflict': True,
            'message': f'This program already has a workout on {calendar_date_str}'
        })
    
    # Create the scheduled day
    scheduled_day = ScheduledDay(
        user_id=current_user.id,
        program_id=instance.program_id,
        program_day_id=program_day_id,
        instance_id=instance_id,
        gym_id=instance.gym_id,
        calendar_date=calendar_date
    )
    db.session.add(scheduled_day)
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/instance/<int:instance_id>/workout-plan')
@login_required
def instance_workout_plan(instance_id):
    """View and edit workout plan for a specific program instance"""
    instance = ProgramInstance.query.filter_by(
        id=instance_id,
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('calendar/instance_workout_plan.html', instance=instance)


@bp.route('/instance/<int:instance_id>/workout-data')
@login_required
def get_instance_workout_data(instance_id):
    """Get workout data for instance with custom weights"""
    instance = ProgramInstance.query.filter_by(
        id=instance_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Get existing custom weights
    custom_weights_map = {}
    for cw in instance.custom_weights:
        custom_weights_map[cw.program_exercise_id] = {
            'weights': json.loads(cw.custom_weights) if cw.custom_weights else [],
            'notes': cw.notes
        }
    
    # Get all scheduled days for this instance to check completion status
    scheduled_days = ScheduledDay.query.filter_by(
        user_id=current_user.id,
        instance_id=instance.id
    ).all()
    
    # Map program_day_id to scheduled day info and get workout sessions
    scheduled_day_map = {}
    scheduled_day_ids = []
    for sd in scheduled_days:
        scheduled_day_map[sd.program_day_id] = {
            'scheduled_date': sd.calendar_date.strftime('%Y-%m-%d'),
            'is_completed': sd.is_completed,
            'scheduled_day_id': sd.id
        }
        scheduled_day_ids.append(sd.id)
    
    # Get all workout sessions for this instance's scheduled days
    workout_sessions = WorkoutSession.query.filter(
        WorkoutSession.scheduled_day_id.in_(scheduled_day_ids)
    ).order_by(WorkoutSession.started_at.desc()).all()
    
    # Map scheduled_day_id to the most recent session
    session_map = {}
    for ws in workout_sessions:
        if ws.scheduled_day_id not in session_map:
            session_map[ws.scheduled_day_id] = ws
    
    # Get all logged sets for these sessions
    session_ids = [ws.id for ws in workout_sessions]
    workout_sets = WorkoutSet.query.filter(
        WorkoutSet.workout_session_id.in_(session_ids)
    ).all() if session_ids else []
    
    # Map (session_id, exercise_id, set_number) to logged weight/reps
    logged_sets_map = {}
    for ws in workout_sets:
        key = (ws.workout_session_id, ws.exercise_id, ws.set_number)
        logged_sets_map[key] = {
            'set_id': ws.id,
            'weight': ws.weight,
            'reps': ws.reps,
            'rpe': ws.rpe,
            'overall_rpe': ws.overall_rpe,
            'completed_at': ws.completed_at.isoformat() if ws.completed_at else None
        }
    
    # Build map of which session has actual logged sets for each scheduled_day
    # (in case there are multiple sessions but only one has data)
    session_with_data = {}
    for ws in workout_sets:
        session = next((s for s in workout_sessions if s.id == ws.workout_session_id), None)
        if session and session.scheduled_day_id:
            session_with_data[session.scheduled_day_id] = session
    
    # Use session with data if available, otherwise use most recent
    for sd_id in scheduled_day_ids:
        if sd_id in session_with_data:
            session_map[sd_id] = session_with_data[sd_id]
    
    # Build workout structure
    weeks_data = []
    for week in instance.program.weeks:
        days_data = []
        for day in week.days:
            day_completion = scheduled_day_map.get(day.id, {})
            scheduled_day_id = day_completion.get('scheduled_day_id')
            session = session_map.get(scheduled_day_id) if scheduled_day_id else None
            
            series_data = []
            for series in day.series:
                exercises_data = []
                for prog_ex in series.exercises:
                    # Get custom weights if exist, otherwise use defaults
                    if prog_ex.id in custom_weights_map:
                        weights = custom_weights_map[prog_ex.id]['weights']
                        notes = custom_weights_map[prog_ex.id]['notes']
                    else:
                        # Use default weights from program
                        weights = json.loads(prog_ex.starting_weights) if prog_ex.starting_weights else []
                        notes = None
                    
                    # Get actual logged weights if session exists
                    logged_weights = []
                    logged_reps = []
                    logged_set_ids = []
                    logged_rpes = []
                    if session:
                        for i in range(prog_ex.sets):
                            key = (session.id, prog_ex.exercise_id, i + 1)
                            if key in logged_sets_map:
                                logged_weights.append(logged_sets_map[key]['weight'])
                                logged_reps.append(logged_sets_map[key]['reps'])
                                logged_set_ids.append(logged_sets_map[key]['set_id'])
                                logged_rpes.append(logged_sets_map[key]['rpe'])
                            else:
                                logged_weights.append(None)
                                logged_reps.append(None)
                                logged_set_ids.append(None)
                                logged_rpes.append(None)
                    
                    exercises_data.append({
                        'id': prog_ex.id,
                        'exercise_id': prog_ex.exercise_id,
                        'exercise_name': prog_ex.exercise.name,
                        'sets': prog_ex.sets,
                        'reps': prog_ex.reps,
                        'weights': weights,
                        'logged_weights': logged_weights if session else None,
                        'logged_reps': logged_reps if session else None,
                        'logged_set_ids': logged_set_ids if session else None,
                        'logged_rpes': logged_rpes if session else None,
                        'session_id': session.id if session else None,
                        'session_completed_at': session.completed_at.isoformat() if session and session.completed_at else None,
                        'notes': notes,
                        'superset_position': prog_ex.superset_position
                    })
                
                series_data.append({
                    'id': series.id,
                    'series_type': series.series_type,
                    'exercises': exercises_data
                })
            
            # Add completion info for this day
            days_data.append({
                'id': day.id,
                'name': day.day_name or f'Day {day.day_number}',
                'series': series_data,
                'scheduled_date': day_completion.get('scheduled_date'),
                'is_completed': day_completion.get('is_completed', False)
            })
        
        weeks_data.append({
            'week_number': week.week_number,
            'days': days_data
        })
    
    return jsonify({
        'program_name': instance.program.name,
        'gym_name': instance.gym.name if instance.gym else None,
        'scheduled_date': instance.scheduled_date.strftime('%Y-%m-%d'),
        'weeks': weeks_data
    })


@bp.route('/instance/<int:instance_id>/update-weights', methods=['POST'])
@login_required
def update_instance_weights(instance_id):
    """Update custom weights for a program exercise in this instance"""
    instance = ProgramInstance.query.filter_by(
        id=instance_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    program_exercise_id = data.get('program_exercise_id')
    custom_weights = data.get('weights', [])
    notes = data.get('notes', '')
    
    if not program_exercise_id:
        return jsonify({'success': False, 'error': 'Missing program_exercise_id'}), 400
    
    # Check if custom weight record exists
    custom_weight = InstanceExerciseWeight.query.filter_by(
        instance_id=instance_id,
        program_exercise_id=program_exercise_id
    ).first()
    
    if custom_weight:
        # Update existing
        custom_weight.custom_weights = json.dumps(custom_weights)
        custom_weight.notes = notes
    else:
        # Create new
        custom_weight = InstanceExerciseWeight(
            instance_id=instance_id,
            program_exercise_id=program_exercise_id,
            custom_weights=json.dumps(custom_weights),
            notes=notes
        )
        db.session.add(custom_weight)
    
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/workout-set/<int:set_id>/update', methods=['POST'])
@login_required
def update_workout_set(set_id):
    """Update a logged workout set"""
    workout_set = WorkoutSet.query.get_or_404(set_id)
    
    # Verify the user owns this workout set through the session
    session = WorkoutSession.query.get(workout_set.workout_session_id)
    if not session or session.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update the fields
    if 'weight' in data:
        workout_set.weight = float(data['weight']) if data['weight'] else None
    if 'reps' in data:
        workout_set.reps = int(data['reps']) if data['reps'] else None
    if 'rpe' in data:
        workout_set.rpe = data['rpe'] if data['rpe'] else None
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'set': {
            'id': workout_set.id,
            'weight': workout_set.weight,
            'reps': workout_set.reps,
            'rpe': workout_set.rpe
        }
    })


