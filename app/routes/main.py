from flask import Blueprint, render_template, send_from_directory, current_app
from flask_login import login_required, current_user
from app.models import ScheduledDay, WorkoutSession, ProgramInstance
from datetime import date, timedelta
from sqlalchemy import func
from sqlalchemy.orm import joinedload
import os

bp = Blueprint('main', __name__)


@bp.route('/')
@login_required
def index():
    """Dashboard / home page - Optimized with eager loading"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Today's workout with eager loading
    todays_workout = ScheduledDay.query.filter_by(
        user_id=current_user.id,
        calendar_date=today
    ).options(
        joinedload(ScheduledDay.program),
        joinedload(ScheduledDay.program_day),
        joinedload(ScheduledDay.gym)
    ).first()
    
    # Recent activity (last completed workout) with eager loading
    recent_workout = ScheduledDay.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).options(
        joinedload(ScheduledDay.program),
        joinedload(ScheduledDay.program_day),
        joinedload(ScheduledDay.gym)
    ).order_by(ScheduledDay.calendar_date.desc()).first()
    
    # Upcoming workouts (next 7 days) with eager loading
    upcoming_workouts = ScheduledDay.query.filter(
        ScheduledDay.user_id == current_user.id,
        ScheduledDay.calendar_date > today,
        ScheduledDay.calendar_date <= today + timedelta(days=7)
    ).options(
        joinedload(ScheduledDay.program),
        joinedload(ScheduledDay.program_day),
        joinedload(ScheduledDay.gym)
    ).order_by(ScheduledDay.calendar_date).limit(5).all()
    
    # Quick stats - already optimized (using count())
    workouts_this_week = ScheduledDay.query.filter(
        ScheduledDay.user_id == current_user.id,
        ScheduledDay.calendar_date >= week_start,
        ScheduledDay.calendar_date <= week_end,
        ScheduledDay.is_completed == True
    ).count()
    
    total_workouts = ScheduledDay.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).count()
    
    active_programs = ProgramInstance.query.filter_by(
        user_id=current_user.id
    ).count()
    
    # Calculate current streak - Optimized to limit lookback
    # Check last 365 days max to prevent infinite loop
    streak = 0
    check_date = today
    max_days_back = 365
    days_checked = 0
    
    while days_checked < max_days_back:
        workout = ScheduledDay.query.filter_by(
            user_id=current_user.id,
            calendar_date=check_date,
            is_completed=True
        ).first()
        if workout:
            streak += 1
            check_date -= timedelta(days=1)
            days_checked += 1
        else:
            # Stop on first missed day
            break
    
    return render_template('main/dashboard.html',
                         todays_workout=todays_workout,
                         recent_workout=recent_workout,
                         upcoming_workouts=upcoming_workouts,
                         workouts_this_week=workouts_this_week,
                         total_workouts=total_workouts,
                         active_programs=active_programs,
                         streak=streak)


# ============================================
# PWA Routes
# ============================================

@bp.route('/sw.js')
def service_worker():
    """Serve service worker with correct MIME type and no caching"""
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'sw.js',
        mimetype='application/javascript'
    )


@bp.route('/manifest.json')
def manifest():
    """Serve PWA manifest with correct MIME type"""
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'manifest.json',
        mimetype='application/manifest+json'
    )
