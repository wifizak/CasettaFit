from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from app.models import UserGoal, UserProfile, BodyMetricHistory
from app.forms import UserGoalForm, BodyMetricForm

bp = Blueprint('goals', __name__, url_prefix='/goals')


@bp.route('/')
@login_required
def index():
    """Goals dashboard showing targets and progress"""
    
    # Get or create user goal
    goal = UserGoal.query.filter_by(user_id=current_user.id).first()
    
    # Get current profile
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    # Get latest body metrics from history
    latest_metric = BodyMetricHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(BodyMetricHistory.recorded_at.desc()).first()
    
    # Get first body metrics for comparison
    first_metric = BodyMetricHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(BodyMetricHistory.recorded_at.asc()).first()
    
    # Calculate BMI if weight and height are available
    current_bmi = None
    target_bmi = None
    # Note: We don't have height in the model yet, but we can add it later
    
    # Calculate progress percentages
    progress = {}
    if goal:
        # Weight progress
        if goal.target_weight and profile and profile.current_weight:
            if first_metric and first_metric.weight:
                start_weight = first_metric.weight
                current_weight = profile.current_weight
                target_weight = goal.target_weight
                
                total_change_needed = target_weight - start_weight
                current_change = current_weight - start_weight
                
                if total_change_needed != 0:
                    progress['weight_percent'] = (current_change / total_change_needed) * 100
                else:
                    progress['weight_percent'] = 100
                
                progress['weight_remaining'] = target_weight - current_weight
            else:
                progress['weight_percent'] = 0
                progress['weight_remaining'] = goal.target_weight - (profile.current_weight or 0)
        
        # Body fat progress
        if goal.target_body_fat and profile and profile.current_body_fat:
            if first_metric and first_metric.body_fat:
                start_bf = first_metric.body_fat
                current_bf = profile.current_body_fat
                target_bf = goal.target_body_fat
                
                total_change_needed = target_bf - start_bf
                current_change = current_bf - start_bf
                
                if total_change_needed != 0:
                    progress['body_fat_percent'] = (current_change / total_change_needed) * 100
                else:
                    progress['body_fat_percent'] = 100
                
                progress['body_fat_remaining'] = target_bf - current_bf
            else:
                progress['body_fat_percent'] = 0
                progress['body_fat_remaining'] = goal.target_body_fat - (profile.current_body_fat or 0)
    
    # Get metric history for charts (last 30 entries)
    metric_history_chart = BodyMetricHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(BodyMetricHistory.recorded_at.desc()).limit(30).all()
    metric_history_chart.reverse()  # Show oldest to newest for chart
    
    # Convert metric history to JSON-serializable format for charts
    metric_history_data = [{
        'id': m.id,
        'weight': m.weight,
        'body_fat': m.body_fat,
        'recorded_at': m.recorded_at.isoformat() if m.recorded_at else None
    } for m in metric_history_chart]
    
    # Get ALL metric history for table (most recent first)
    all_metric_history = BodyMetricHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(BodyMetricHistory.recorded_at.desc()).all()
    
    return render_template('goals/index.html',
                         goal=goal,
                         profile=profile,
                         latest_metric=latest_metric,
                         first_metric=first_metric,
                         progress=progress,
                         metric_history=metric_history_data,
                         all_metric_history=all_metric_history,
                         today=date.today())


@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """Edit user goals"""
    
    goal = UserGoal.query.filter_by(user_id=current_user.id).first()
    
    if not goal:
        goal = UserGoal(user_id=current_user.id)
        db.session.add(goal)
    
    form = UserGoalForm()
    
    if form.validate_on_submit():
        goal.target_weight = form.target_weight.data
        goal.target_body_fat = form.target_body_fat.data
        goal.target_date = form.target_date.data
        goal.target_chest = form.target_chest.data
        goal.target_waist = form.target_waist.data
        goal.target_hips = form.target_hips.data
        goal.target_left_arm = form.target_left_arm.data
        goal.target_right_arm = form.target_right_arm.data
        goal.target_left_thigh = form.target_left_thigh.data
        goal.target_right_thigh = form.target_right_thigh.data
        goal.target_left_calf = form.target_left_calf.data
        goal.target_right_calf = form.target_right_calf.data
        goal.notes = form.notes.data
        
        db.session.commit()
        flash('Goals updated successfully!', 'success')
        return redirect(url_for('goals.index'))
    
    elif request.method == 'GET':
        form.target_weight.data = goal.target_weight
        form.target_body_fat.data = goal.target_body_fat
        form.target_date.data = goal.target_date
        form.target_chest.data = goal.target_chest
        form.target_waist.data = goal.target_waist
        form.target_hips.data = goal.target_hips
        form.target_left_arm.data = goal.target_left_arm
        form.target_right_arm.data = goal.target_right_arm
        form.target_left_thigh.data = goal.target_left_thigh
        form.target_right_thigh.data = goal.target_right_thigh
        form.target_left_calf.data = goal.target_left_calf
        form.target_right_calf.data = goal.target_right_calf
        form.notes.data = goal.notes
    
    return render_template('goals/edit.html', form=form, goal=goal)


@bp.route('/log-metrics', methods=['GET', 'POST'])
@login_required
def log_metrics():
    """Log body metrics"""
    
    form = BodyMetricForm()
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
    
    if form.validate_on_submit():
        # Create history entry
        metric = BodyMetricHistory(
            user_id=current_user.id,
            weight=form.weight.data,
            body_fat=form.body_fat.data,
            chest=form.chest.data,
            waist=form.waist.data,
            hips=form.hips.data,
            left_arm=form.left_arm.data,
            right_arm=form.right_arm.data,
            left_thigh=form.left_thigh.data,
            right_thigh=form.right_thigh.data,
            left_calf=form.left_calf.data,
            right_calf=form.right_calf.data,
            notes=form.notes.data
        )
        db.session.add(metric)
        
        # Update current profile
        if form.weight.data:
            profile.current_weight = form.weight.data
        if form.body_fat.data:
            profile.current_body_fat = form.body_fat.data
        if form.chest.data:
            profile.chest = form.chest.data
        if form.waist.data:
            profile.waist = form.waist.data
        if form.hips.data:
            profile.hips = form.hips.data
        if form.left_arm.data:
            profile.left_arm = form.left_arm.data
        if form.right_arm.data:
            profile.right_arm = form.right_arm.data
        if form.left_thigh.data:
            profile.left_thigh = form.left_thigh.data
        if form.right_thigh.data:
            profile.right_thigh = form.right_thigh.data
        if form.left_calf.data:
            profile.left_calf = form.left_calf.data
        if form.right_calf.data:
            profile.right_calf = form.right_calf.data
        
        db.session.commit()
        flash('Body metrics logged successfully!', 'success')
        return redirect(url_for('goals.index'))
    
    elif request.method == 'GET':
        # Pre-fill with current values
        form.weight.data = profile.current_weight
        form.body_fat.data = profile.current_body_fat
        form.chest.data = profile.chest
        form.waist.data = profile.waist
        form.hips.data = profile.hips
        form.left_arm.data = profile.left_arm
        form.right_arm.data = profile.right_arm
        form.left_thigh.data = profile.left_thigh
        form.right_thigh.data = profile.right_thigh
        form.left_calf.data = profile.left_calf
        form.right_calf.data = profile.right_calf
    
    return render_template('goals/log_metrics.html', form=form, profile=profile)


@bp.route('/history')
@login_required
def history():
    """View all logged body metrics"""
    
    metrics = BodyMetricHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(BodyMetricHistory.recorded_at.desc()).all()
    
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    return render_template('goals/history.html', metrics=metrics, profile=profile)


@bp.route('/api/metrics-chart')
@login_required
def metrics_chart():
    """Get body metrics data for charts"""
    
    metrics = BodyMetricHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(BodyMetricHistory.recorded_at.asc()).all()
    
    return jsonify([{
        'date': m.recorded_at.strftime('%Y-%m-%d'),
        'weight': m.weight,
        'body_fat': m.body_fat,
        'chest': m.chest,
        'waist': m.waist,
        'hips': m.hips
    } for m in metrics])
