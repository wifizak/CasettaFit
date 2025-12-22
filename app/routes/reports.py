from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func, distinct, desc
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from app import db
from app.models import (WorkoutSession, WorkoutSet, ScheduledDay, MasterExercise, 
                        BodyMetricHistory, UserProfile, ProgramInstance)

bp = Blueprint('reports', __name__, url_prefix='/reports')


@bp.route('/')
@login_required
def index():
    """Reports dashboard with analytics and insights
    
    Note: This route is already well-optimized using SQL aggregation functions
    to minimize queries. Most queries use GROUP BY, COUNT, and SUM at the DB level.
    """
    
    # ========================================
    # Workout Completion Statistics
    # ========================================
    
    # Total completed workouts
    total_workouts = WorkoutSession.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).count()
    
    # Total completed scheduled days (can be different from sessions if multiple sessions per day)
    total_days = ScheduledDay.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).count()
    
    # Completed programs (instances where all scheduled days are completed)
    # Optimized: Use subquery to count completion status
    completed_programs = db.session.query(
        ProgramInstance.id
    ).filter(
        ProgramInstance.user_id == current_user.id,
        # Subquery: instance has at least one scheduled day
        ProgramInstance.id.in_(
            db.session.query(ScheduledDay.instance_id).filter(
                ScheduledDay.instance_id.isnot(None)
            )
        ),
        # Subquery: all scheduled days for instance are completed
        ~ProgramInstance.id.in_(
            db.session.query(ScheduledDay.instance_id).filter(
                ScheduledDay.instance_id.isnot(None),
                ScheduledDay.is_completed == False
            )
        )
    ).count()
    
    # Total sets completed
    total_sets = db.session.query(func.count(WorkoutSet.id)).join(
        WorkoutSession
    ).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.is_completed == True
    ).scalar() or 0
    
    # ========================================
    # Progressive Overload Analysis
    # ========================================
    
    # Get top 5 exercises by volume (weight x reps)
    top_exercises = db.session.query(
        MasterExercise.name,
        MasterExercise.id,
        func.sum(WorkoutSet.weight * WorkoutSet.reps).label('total_volume'),
        func.count(WorkoutSet.id).label('set_count')
    ).join(
        WorkoutSet, WorkoutSet.exercise_id == MasterExercise.id
    ).join(
        WorkoutSession, WorkoutSet.workout_session_id == WorkoutSession.id
    ).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.is_completed == True,
        WorkoutSet.weight.isnot(None),
        WorkoutSet.reps.isnot(None)
    ).group_by(
        MasterExercise.id, MasterExercise.name
    ).order_by(
        desc('total_volume')
    ).limit(5).all()
    
    # Calculate progressive overload for top exercises
    exercise_progress = []
    for exercise in top_exercises:
        # Get first and last workout data for this exercise
        first_set = WorkoutSet.query.join(
            WorkoutSession
        ).filter(
            WorkoutSession.user_id == current_user.id,
            WorkoutSet.exercise_id == exercise.id,
            WorkoutSet.weight.isnot(None),
            WorkoutSet.reps.isnot(None)
        ).order_by(WorkoutSet.completed_at.asc()).first()
        
        last_set = WorkoutSet.query.join(
            WorkoutSession
        ).filter(
            WorkoutSession.user_id == current_user.id,
            WorkoutSet.exercise_id == exercise.id,
            WorkoutSet.weight.isnot(None),
            WorkoutSet.reps.isnot(None)
        ).order_by(WorkoutSet.completed_at.desc()).first()
        
        if first_set and last_set and first_set.id != last_set.id:
            first_volume = first_set.weight * first_set.reps
            last_volume = last_set.weight * last_set.reps
            volume_change = last_volume - first_volume
            percent_change = ((last_volume - first_volume) / first_volume * 100) if first_volume > 0 else 0
            
            exercise_progress.append({
                'name': exercise.name,
                'id': exercise.id,
                'total_volume': exercise.total_volume,
                'set_count': exercise.set_count,
                'first_weight': first_set.weight,
                'last_weight': last_set.weight,
                'first_reps': first_set.reps,
                'last_reps': last_set.reps,
                'volume_change': volume_change,
                'percent_change': percent_change,
                'first_date': first_set.completed_at,
                'last_date': last_set.completed_at
            })
        else:
            exercise_progress.append({
                'name': exercise.name,
                'id': exercise.id,
                'total_volume': exercise.total_volume,
                'set_count': exercise.set_count,
                'first_weight': None,
                'last_weight': None,
                'volume_change': 0,
                'percent_change': 0
            })
    
    # Overall progressive overload (total volume over time)
    # Compare last 30 days vs previous 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    sixty_days_ago = datetime.utcnow() - timedelta(days=60)
    
    recent_volume = db.session.query(
        func.sum(WorkoutSet.weight * WorkoutSet.reps)
    ).join(
        WorkoutSession
    ).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.is_completed == True,
        WorkoutSession.completed_at >= thirty_days_ago,
        WorkoutSet.weight.isnot(None),
        WorkoutSet.reps.isnot(None)
    ).scalar() or 0
    
    previous_volume = db.session.query(
        func.sum(WorkoutSet.weight * WorkoutSet.reps)
    ).join(
        WorkoutSession
    ).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.is_completed == True,
        WorkoutSession.completed_at >= sixty_days_ago,
        WorkoutSession.completed_at < thirty_days_ago,
        WorkoutSet.weight.isnot(None),
        WorkoutSet.reps.isnot(None)
    ).scalar() or 0
    
    overall_progress = {
        'recent_volume': recent_volume,
        'previous_volume': previous_volume,
        'volume_change': recent_volume - previous_volume,
        'percent_change': ((recent_volume - previous_volume) / previous_volume * 100) if previous_volume > 0 else 0
    }
    
    # ========================================
    # Body Metrics Tracking
    # ========================================
    
    # Get current metrics from profile
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    # Get latest body metrics from history
    latest_metric = BodyMetricHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(desc(BodyMetricHistory.recorded_at)).first()
    
    # Get oldest body metrics for comparison
    oldest_metric = BodyMetricHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(BodyMetricHistory.recorded_at.asc()).first()
    
    # Calculate body metric changes
    body_metrics = {
        'current_weight': profile.current_weight if profile else None,
        'current_body_fat': profile.current_body_fat if profile else None,
        'weight_unit': profile.weight_unit if profile else 'lbs',
        'has_history': latest_metric is not None
    }
    
    if latest_metric and oldest_metric and latest_metric.id != oldest_metric.id:
        weight_change = (latest_metric.weight or 0) - (oldest_metric.weight or 0)
        body_fat_change = (latest_metric.body_fat or 0) - (oldest_metric.body_fat or 0)
        
        body_metrics.update({
            'weight_change': weight_change,
            'body_fat_change': body_fat_change,
            'first_weight': oldest_metric.weight,
            'latest_weight': latest_metric.weight,
            'first_body_fat': oldest_metric.body_fat,
            'latest_body_fat': latest_metric.body_fat,
            'first_date': oldest_metric.recorded_at,
            'latest_date': latest_metric.recorded_at
        })
    
    # ========================================
    # Activity Trends
    # ========================================
    
    # Workouts per week over last 12 weeks
    twelve_weeks_ago = datetime.utcnow() - timedelta(weeks=12)
    
    weekly_workouts = db.session.query(
        func.strftime('%Y-%W', WorkoutSession.completed_at).label('week'),
        func.count(WorkoutSession.id).label('workout_count')
    ).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSession.is_completed == True,
        WorkoutSession.completed_at >= twelve_weeks_ago
    ).group_by('week').order_by('week').all()
    
    return render_template('reports/index.html',
                         total_workouts=total_workouts,
                         total_days=total_days,
                         completed_programs=completed_programs,
                         total_sets=total_sets,
                         exercise_progress=exercise_progress,
                         overall_progress=overall_progress,
                         body_metrics=body_metrics,
                         weekly_workouts=weekly_workouts)


@bp.route('/api/exercise-history/<int:exercise_id>')
@login_required
def exercise_history(exercise_id):
    """Get detailed history for a specific exercise (for charts)"""
    
    # Get all sets for this exercise over time
    sets = db.session.query(
        WorkoutSet.completed_at,
        WorkoutSet.weight,
        WorkoutSet.reps,
        WorkoutSet.set_number
    ).join(
        WorkoutSession
    ).filter(
        WorkoutSession.user_id == current_user.id,
        WorkoutSet.exercise_id == exercise_id,
        WorkoutSet.weight.isnot(None),
        WorkoutSet.reps.isnot(None)
    ).order_by(WorkoutSet.completed_at.asc()).all()
    
    # Group by session (date) and calculate max weight per session
    history = {}
    for set_data in sets:
        date_key = set_data.completed_at.strftime('%Y-%m-%d')
        if date_key not in history:
            history[date_key] = {
                'date': date_key,
                'max_weight': set_data.weight,
                'total_volume': set_data.weight * set_data.reps,
                'sets': []
            }
        else:
            history[date_key]['max_weight'] = max(history[date_key]['max_weight'], set_data.weight)
            history[date_key]['total_volume'] += set_data.weight * set_data.reps
        
        history[date_key]['sets'].append({
            'weight': set_data.weight,
            'reps': set_data.reps,
            'set_number': set_data.set_number
        })
    
    return jsonify(list(history.values()))


@bp.route('/api/body-metrics-history')
@login_required
def body_metrics_history():
    """Get body metrics history over time (for charts)"""
    
    metrics = BodyMetricHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(BodyMetricHistory.recorded_at.asc()).all()
    
    return jsonify([{
        'date': m.recorded_at.strftime('%Y-%m-%d'),
        'weight': m.weight,
        'body_fat': m.body_fat,
        'chest': m.chest,
        'waist': m.waist,
        'hips': m.hips,
        'left_arm': m.left_arm,
        'right_arm': m.right_arm
    } for m in metrics])
