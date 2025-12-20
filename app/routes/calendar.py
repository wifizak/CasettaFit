from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app import db
from app.models import Program, ProgramWeek, ProgramDay, ProgramSeries, ProgramExercise, ScheduledDay
import json

bp = Blueprint('calendar', __name__, url_prefix='/calendar')


@bp.route('/')
@login_required
def index():
    """Main calendar view"""
    programs = Program.query.filter_by(created_by=current_user.id).order_by(Program.name).all()
    return render_template('calendar/index.html', programs=programs)


@bp.route('/events')
@login_required
def get_events():
    """Get all scheduled workouts as FullCalendar events"""
    scheduled_days = ScheduledDay.query.filter_by(
        user_id=current_user.id
    ).order_by(ScheduledDay.calendar_date).all()
    
    events = []
    for sd in scheduled_days:
        events.append({
            'id': sd.id,
            'title': f"{sd.program.name} - {sd.program_day.day_name or 'Day ' + str(sd.program_day.day_number)}",
            'start': sd.calendar_date.isoformat(),
            'allDay': True,
            'extendedProps': {
                'programId': sd.program_id,
                'programDayId': sd.program_day_id,
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
    
    # Create scheduled days
    for mapping in mappings:
        calendar_date = datetime.strptime(mapping['calendar_date'], '%Y-%m-%d').date()
        program_day_id = mapping['program_day_id']
        
        scheduled_day = ScheduledDay(
            user_id=current_user.id,
            program_id=program_id,
            program_day_id=program_day_id,
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
    
    # Get series and exercises for this day
    series_data = []
    for series in scheduled_day.program_day.series:
        exercises_data = []
        for prog_ex in series.exercises:
            starting_weights = []
            if prog_ex.starting_weights:
                try:
                    starting_weights = json.loads(prog_ex.starting_weights)
                except:
                    pass
            
            exercises_data.append({
                'exercise_name': prog_ex.exercise.name,
                'sets': prog_ex.sets,
                'reps': prog_ex.reps,
                'starting_weights': starting_weights,
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
        'calendar_date': scheduled_day.calendar_date.strftime('%Y-%m-%d'),
        'is_completed': scheduled_day.is_completed,
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
