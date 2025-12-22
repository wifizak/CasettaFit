from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import ScheduledDay, WorkoutSession, ProgramInstance
from datetime import date, timedelta
from sqlalchemy import func

bp = Blueprint('main', __name__)


@bp.route('/')
@login_required
def index():
    """Dashboard / home page"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Today's workout
    todays_workout = ScheduledDay.query.filter_by(
        user_id=current_user.id,
        calendar_date=today
    ).first()
    
    # Recent activity (last completed workout)
    recent_workout = ScheduledDay.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).order_by(ScheduledDay.calendar_date.desc()).first()
    
    # Upcoming workouts (next 7 days)
    upcoming_workouts = ScheduledDay.query.filter(
        ScheduledDay.user_id == current_user.id,
        ScheduledDay.calendar_date > today,
        ScheduledDay.calendar_date <= today + timedelta(days=7)
    ).order_by(ScheduledDay.calendar_date).limit(5).all()
    
    # Quick stats
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
    
    # Calculate current streak
    streak = 0
    check_date = today
    while True:
        workout = ScheduledDay.query.filter_by(
            user_id=current_user.id,
            calendar_date=check_date,
            is_completed=True
        ).first()
        if workout:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    return render_template('main/dashboard.html',
                         todays_workout=todays_workout,
                         recent_workout=recent_workout,
                         upcoming_workouts=upcoming_workouts,
                         workouts_this_week=workouts_this_week,
                         total_workouts=total_workouts,
                         active_programs=active_programs,
                         streak=streak)
