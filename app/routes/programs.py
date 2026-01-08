from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
import json
from app import db
from app.models import (Program, ProgramWeek, ProgramDay, ProgramExercise, 
                        ProgramSeries, ProgramShare, BodyPattern, MasterExercise, User)
from app.forms import (ProgramForm, ProgramWeekForm, ProgramDayForm, 
                       ProgramExerciseForm, ProgramSeriesForm, BodyPatternForm, ProgramShareForm)

bp = Blueprint('programs', __name__, url_prefix='/programs')


@bp.route('/')
@login_required
def index():
    """List user's programs"""
    # User's own programs
    my_programs = Program.query.filter_by(created_by=current_user.id).order_by(Program.updated_at.desc()).all()
    
    # Programs shared with user
    shared_program_ids = [ps.program_id for ps in ProgramShare.query.filter_by(shared_with_user_id=current_user.id).all()]
    shared_programs = Program.query.filter(Program.id.in_(shared_program_ids)).all() if shared_program_ids else []
    
    # Admin templates (if not admin, only show templates)
    templates = Program.query.filter_by(is_template=True).all()
    
    return render_template('programs/index.html', 
                         my_programs=my_programs,
                         shared_programs=shared_programs,
                         templates=templates)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new program"""
    form = ProgramForm()
    
    if form.validate_on_submit():
        # Only admins can create templates
        is_template = form.is_template.data if current_user.is_admin else False
        
        program = Program(
            name=form.name.data,
            description=form.description.data,
            duration_weeks=form.duration_weeks.data,
            days_per_week=form.days_per_week.data,
            notes=form.notes.data,
            created_by=current_user.id,
            is_template=is_template
        )
        
        db.session.add(program)
        db.session.flush()
        
        # Create default weeks structure
        for week_num in range(1, form.duration_weeks.data + 1):
            week = ProgramWeek(
                program_id=program.id,
                week_number=week_num
            )
            db.session.add(week)
            db.session.flush()
            
            # Create days based on days_per_week setting
            for day_num in range(1, form.days_per_week.data + 1):
                day = ProgramDay(
                    week_id=week.id,
                    day_number=day_num
                )
                db.session.add(day)
        
        db.session.commit()
        
        flash(f'Program "{program.name}" created successfully! Now add exercises to your days.', 'success')
        return redirect(url_for('programs.view', program_id=program.id))
    
    return render_template('programs/create.html', form=form)


@bp.route('/<int:program_id>')
@login_required
def view(program_id):
    """View program details"""
    program = Program.query.get_or_404(program_id)
    
    # Check permissions
    can_view = (
        program.created_by == current_user.id or
        program.is_template or
        ProgramShare.query.filter_by(program_id=program.id, shared_with_user_id=current_user.id).first() is not None
    )
    
    if not can_view:
        flash('You do not have access to this program.', 'danger')
        return redirect(url_for('programs.index'))
    
    # Check if user can edit
    can_edit = program.created_by == current_user.id
    
    return render_template('programs/view.html', program=program, can_edit=can_edit)


@bp.route('/<int:program_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(program_id):
    """Edit program"""
    program = Program.query.get_or_404(program_id)
    
    # Check permissions
    if program.created_by != current_user.id:
        flash('You do not have permission to edit this program.', 'danger')
        return redirect(url_for('programs.index'))
    
    form = ProgramForm()
    
    if form.validate_on_submit():
        program.name = form.name.data
        program.description = form.description.data
        program.duration_weeks = form.duration_weeks.data
        program.days_per_week = form.days_per_week.data
        program.notes = form.notes.data
        
        if current_user.is_admin:
            program.is_template = form.is_template.data
        
        db.session.commit()
        flash(f'Program "{program.name}" updated successfully!', 'success')
        return redirect(url_for('programs.view', program_id=program.id))
    
    elif request.method == 'GET':
        form.name.data = program.name
        form.description.data = program.description
        form.duration_weeks.data = program.duration_weeks
        form.days_per_week.data = program.days_per_week
        form.notes.data = program.notes
        form.is_template.data = program.is_template
    
    return render_template('programs/edit.html', form=form, program=program)


@bp.route('/<int:program_id>/delete', methods=['POST'])
@login_required
def delete(program_id):
    """Delete program"""
    program = Program.query.get_or_404(program_id)
    
    # Check permissions
    if program.created_by != current_user.id:
        flash('You do not have permission to delete this program.', 'danger')
        return redirect(url_for('programs.index'))
    
    name = program.name
    db.session.delete(program)
    db.session.commit()
    
    flash(f'Program "{name}" deleted successfully.', 'success')
    return redirect(url_for('programs.index'))


@bp.route('/<int:program_id>/duplicate', methods=['POST'])
@login_required
def duplicate(program_id):
    """Duplicate a program (create a local copy)"""
    original = Program.query.get_or_404(program_id)
    
    # Check if user can view this program
    can_view = (
        original.created_by == current_user.id or
        original.is_template or
        ProgramShare.query.filter_by(program_id=original.id, shared_with_user_id=current_user.id).first() is not None
    )
    
    if not can_view:
        flash('You do not have access to this program.', 'danger')
        return redirect(url_for('programs.index'))
    
    # Create new program
    new_program = Program(
        name=f"{original.name} (Copy)",
        description=original.description,
        duration_weeks=original.duration_weeks,
        notes=original.notes,
        created_by=current_user.id,
        is_template=False  # Copies are never templates
    )
    
    db.session.add(new_program)
    db.session.flush()
    
    # Duplicate all weeks, days, and exercises
    for week in original.weeks:
        new_week = ProgramWeek(
            program_id=new_program.id,
            week_number=week.week_number,
            week_name=week.week_name,
            is_deload=week.is_deload,
            notes=week.notes
        )
        db.session.add(new_week)
        db.session.flush()
        
        for day in week.days:
            new_day = ProgramDay(
                week_id=new_week.id,
                day_number=day.day_number,
                day_name=day.day_name,
                is_rest_day=day.is_rest_day,
                has_superset=day.has_superset,
                notes=day.notes
            )
            db.session.add(new_day)
            db.session.flush()
            
            for series in day.series:
                new_series = ProgramSeries(
                    day_id=new_day.id,
                    order_index=series.order_index,
                    series_type=series.series_type,
                    time_seconds=series.time_seconds,
                    notes=series.notes
                )
                db.session.add(new_series)
                db.session.flush()
                
                for exercise in series.exercises:
                    new_exercise = ProgramExercise(
                        series_id=new_series.id,
                        exercise_id=exercise.exercise_id,
                        superset_position=exercise.superset_position,
                        sets=exercise.sets,
                        reps=exercise.reps,
                        lift_time_seconds=exercise.lift_time_seconds,
                        rest_time_seconds=exercise.rest_time_seconds,
                        starting_weights=exercise.starting_weights,
                        target_rpe=exercise.target_rpe,
                        notes=exercise.notes
                    )
                    db.session.add(new_exercise)
    
    db.session.commit()
    
    flash(f'Program duplicated successfully as "{new_program.name}"!', 'success')
    return redirect(url_for('programs.view', program_id=new_program.id))


# Week management
@bp.route('/week/<int:week_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_week(week_id):
    """Edit week details"""
    week = ProgramWeek.query.get_or_404(week_id)
    program = week.program
    
    # Check permissions
    if program.created_by != current_user.id:
        flash('You do not have permission to edit this program.', 'danger')
        return redirect(url_for('programs.index'))
    
    form = ProgramWeekForm()
    
    if form.validate_on_submit():
        week.week_name = form.week_name.data
        week.is_deload = form.is_deload.data
        week.notes = form.notes.data
        db.session.commit()
        
        flash(f'Week {week.week_number} updated successfully!', 'success')
        return redirect(url_for('programs.view', program_id=program.id))
    
    elif request.method == 'GET':
        form.week_name.data = week.week_name
        form.is_deload.data = week.is_deload
        form.notes.data = week.notes
    
    return render_template('programs/edit_week.html', form=form, week=week, program=program)


# Day management
@bp.route('/day/<int:day_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_day(day_id):
    """Edit day details"""
    day = ProgramDay.query.get_or_404(day_id)
    week = day.week
    program = week.program
    
    # Check permissions
    if program.created_by != current_user.id:
        flash('You do not have permission to edit this program.', 'danger')
        return redirect(url_for('programs.index'))
    
    form = ProgramDayForm()
    
    if form.validate_on_submit():
        day.day_name = form.day_name.data
        day.is_rest_day = form.is_rest_day.data
        day.notes = form.notes.data
        db.session.commit()
        
        flash('Day updated successfully!', 'success')
        return redirect(url_for('programs.view', program_id=program.id))
    
    elif request.method == 'GET':
        form.day_name.data = day.day_name
        form.is_rest_day.data = day.is_rest_day
        form.notes.data = day.notes
    
    return render_template('programs/edit_day.html', form=form, day=day, week=week, program=program)


# Series management
@bp.route('/day/<int:day_id>/series/add', methods=['GET', 'POST'])
@login_required
def add_series(day_id):
    """Add series (single or superset) to program day"""
    day = ProgramDay.query.get_or_404(day_id)
    week = day.week
    program = week.program
    
    # Check permissions
    if program.created_by != current_user.id:
        flash('You do not have permission to edit this program.', 'danger')
        return redirect(url_for('programs.index'))
    
    form = ProgramSeriesForm()
    
    # Populate exercises
    exercises = MasterExercise.query.order_by(MasterExercise.name).all()
    form.exercise1_id.choices = [(e.id, e.name) for e in exercises]
    form.exercise2_id.choices = [(0, '-- Select Exercise 2 --')] + [(e.id, e.name) for e in exercises]
    
    if form.validate_on_submit():
        # Get max order index
        max_order = db.session.query(db.func.max(ProgramSeries.order_index)).filter_by(day_id=day.id).scalar() or -1
        
        # Create series
        series = ProgramSeries(
            day_id=day.id,
            order_index=max_order + 1,
            series_type=form.series_type.data,
            time_seconds=form.time_seconds.data if form.time_seconds.data else None,
            notes=form.notes.data
        )
        db.session.add(series)
        db.session.flush()
        
        # Add first exercise
        # Collect weights from individual set inputs
        weights1 = []
        for i in range(1, form.sets.data + 1):
            weight_key = f'weight1_set{i}'
            if weight_key in request.form and request.form[weight_key]:
                weights1.append(float(request.form[weight_key]))
        weights1_json = json.dumps(weights1)
        
        ex1 = ProgramExercise(
            series_id=series.id,
            exercise_id=form.exercise1_id.data,
            superset_position=1,
            sets=form.sets.data,
            reps=form.reps1.data,
            rest_time_seconds=form.rest1_time_seconds.data,
            starting_weights=weights1_json,
            target_rpe=form.target_rpe1.data
        )
        db.session.add(ex1)
        
        # Add second exercise if superset
        if form.series_type.data == 'superset' and form.exercise2_id.data:
            # Collect weights from individual set inputs
            weights2 = []
            for i in range(1, form.sets.data + 1):
                weight_key = f'weight2_set{i}'
                if weight_key in request.form and request.form[weight_key]:
                    weights2.append(float(request.form[weight_key]))
            weights2_json = json.dumps(weights2)
            
            ex2 = ProgramExercise(
                series_id=series.id,
                exercise_id=form.exercise2_id.data,
                superset_position=2,
                sets=form.sets.data,  # Same sets as ex1
                reps=form.reps2.data,
                rest_time_seconds=form.rest2_time_seconds.data,
                starting_weights=weights2_json,
                target_rpe=form.target_rpe2.data
            )
            db.session.add(ex2)
        
        db.session.commit()
        
        flash(f'{"Superset" if form.series_type.data == "superset" else "Exercise"} added to program day!', 'success')
        return redirect(url_for('programs.view', program_id=program.id))
    
    return render_template('programs/add_series.html', form=form, day=day, week=week, program=program)


@bp.route('/series/<int:series_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_series(series_id):
    """Edit existing series"""
    series = ProgramSeries.query.get_or_404(series_id)
    day = series.day
    week = day.week
    program = week.program
    
    # Check permissions
    if program.created_by != current_user.id:
        flash('You do not have permission to edit this program.', 'danger')
        return redirect(url_for('programs.index'))
    
    form = ProgramSeriesForm()
    
    # Populate exercises
    exercises = MasterExercise.query.order_by(MasterExercise.name).all()
    form.exercise1_id.choices = [(e.id, e.name) for e in exercises]
    form.exercise2_id.choices = [(0, '-- Select Exercise 2 --')] + [(e.id, e.name) for e in exercises]
    
    if form.validate_on_submit():
        # Update series
        series.series_type = form.series_type.data
        series.time_seconds = form.time_seconds.data if form.time_seconds.data else None
        series.notes = form.notes.data
        
        # Get existing exercises
        ex1 = series.exercises[0] if len(series.exercises) > 0 else None
        ex2 = series.exercises[1] if len(series.exercises) > 1 else None
        
        # Update first exercise
        if ex1:
            # Collect weights from individual set inputs
            weights1 = []
            for i in range(1, form.sets.data + 1):
                weight_key = f'weight1_set{i}'
                if weight_key in request.form and request.form[weight_key]:
                    weights1.append(float(request.form[weight_key]))
            weights1_json = json.dumps(weights1)
            
            ex1.exercise_id = form.exercise1_id.data
            ex1.sets = form.sets.data
            ex1.reps = form.reps1.data
            ex1.rest_time_seconds = form.rest1_time_seconds.data
            ex1.starting_weights = weights1_json
            ex1.target_rpe = form.target_rpe1.data
        else:
            # Collect weights from individual set inputs
            weights1 = []
            for i in range(1, form.sets.data + 1):
                weight_key = f'weight1_set{i}'
                if weight_key in request.form and request.form[weight_key]:
                    weights1.append(float(request.form[weight_key]))
            weights1_json = json.dumps(weights1)
            
            ex1 = ProgramExercise(
                series_id=series.id,
                exercise_id=form.exercise1_id.data,
                superset_position=1,
                sets=form.sets.data,
                reps=form.reps1.data,
                rest_time_seconds=form.rest1_time_seconds.data,
                starting_weights=weights1_json,
                target_rpe=form.target_rpe1.data
            )
            db.session.add(ex1)
        
        # Handle second exercise for supersets
        if form.series_type.data == 'superset' and form.exercise2_id.data:
            if ex2:
                # Collect weights from individual set inputs
                weights2 = []
                for i in range(1, form.sets.data + 1):
                    weight_key = f'weight2_set{i}'
                    if weight_key in request.form and request.form[weight_key]:
                        weights2.append(float(request.form[weight_key]))
                weights2_json = json.dumps(weights2)
                
                ex2.exercise_id = form.exercise2_id.data
                ex2.sets = form.sets.data
                ex2.reps = form.reps2.data
                ex2.rest_time_seconds = form.rest2_time_seconds.data
                ex2.starting_weights = weights2_json
                ex2.target_rpe = form.target_rpe2.data
            else:
                # Collect weights from individual set inputs
                weights2 = []
                for i in range(1, form.sets.data + 1):
                    weight_key = f'weight2_set{i}'
                    if weight_key in request.form and request.form[weight_key]:
                        weights2.append(float(request.form[weight_key]))
                weights2_json = json.dumps(weights2)
                
                ex2 = ProgramExercise(
                    series_id=series.id,
                    exercise_id=form.exercise2_id.data,
                    superset_position=2,
                    sets=form.sets.data,
                    reps=form.reps2.data,
                    rest_time_seconds=form.rest2_time_seconds.data,
                    starting_weights=weights2_json,
                    target_rpe=form.target_rpe2.data
                )
                db.session.add(ex2)
        else:
            # If changed from superset to single, delete second exercise
            if ex2:
                db.session.delete(ex2)
        
        db.session.commit()
        
        flash('Series updated successfully!', 'success')
        return redirect(url_for('programs.view', program_id=program.id))
    
    # Pre-populate form with existing data
    if request.method == 'GET':
        form.series_type.data = series.series_type
        form.time_seconds.data = series.time_seconds
        form.notes.data = series.notes
        
        if len(series.exercises) > 0:
            ex1 = series.exercises[0]
            form.exercise1_id.data = ex1.exercise_id
            form.sets.data = ex1.sets
            form.reps1.data = ex1.reps
            form.rest1_time_seconds.data = ex1.rest_time_seconds
            # Pass weights as parsed JSON array, not comma-separated string
            if ex1.starting_weights:
                form.starting_weights1.data = ex1.starting_weights  # Keep as JSON string for JS to parse
            form.target_rpe1.data = ex1.target_rpe
        
        if len(series.exercises) > 1:
            ex2 = series.exercises[1]
            form.exercise2_id.data = ex2.exercise_id
            form.reps2.data = ex2.reps
            form.rest2_time_seconds.data = ex2.rest_time_seconds
            # Pass weights as parsed JSON array, not comma-separated string
            if ex2.starting_weights:
                form.starting_weights2.data = ex2.starting_weights  # Keep as JSON string for JS to parse
            form.target_rpe2.data = ex2.target_rpe
    
    return render_template('programs/edit_series.html', form=form, series=series, day=day, week=week, program=program)


@bp.route('/series/<int:series_id>/move-up', methods=['POST'])
@login_required
def move_series_up(series_id):
    """Move series up in the order"""
    series = ProgramSeries.query.get_or_404(series_id)
    day = series.day
    program = day.week.program
    
    # Check permissions
    if program.created_by != current_user.id:
        flash('You do not have permission to edit this program.', 'danger')
        return redirect(url_for('programs.index'))
    
    # Get the series above this one
    series_above = ProgramSeries.query.filter_by(day_id=day.id).filter(
        ProgramSeries.order_index < series.order_index
    ).order_by(ProgramSeries.order_index.desc()).first()
    
    if series_above:
        # Swap order indices
        series.order_index, series_above.order_index = series_above.order_index, series.order_index
        db.session.commit()
        flash('Series moved up.', 'success')
    
    return redirect(url_for('programs.view', program_id=program.id))


@bp.route('/series/<int:series_id>/move-down', methods=['POST'])
@login_required
def move_series_down(series_id):
    """Move series down in the order"""
    series = ProgramSeries.query.get_or_404(series_id)
    day = series.day
    program = day.week.program
    
    # Check permissions
    if program.created_by != current_user.id:
        flash('You do not have permission to edit this program.', 'danger')
        return redirect(url_for('programs.index'))
    
    # Get the series below this one
    series_below = ProgramSeries.query.filter_by(day_id=day.id).filter(
        ProgramSeries.order_index > series.order_index
    ).order_by(ProgramSeries.order_index.asc()).first()
    
    if series_below:
        # Swap order indices
        series.order_index, series_below.order_index = series_below.order_index, series.order_index
        db.session.commit()
        flash('Series moved down.', 'success')
    
    return redirect(url_for('programs.view', program_id=program.id))


@bp.route('/series/<int:series_id>/delete', methods=['POST'])
@login_required
def delete_series(series_id):
    """Delete series from program day"""
    series = ProgramSeries.query.get_or_404(series_id)
    day = series.day
    program = day.week.program
    
    # Check permissions
    if program.created_by != current_user.id:
        flash('You do not have permission to edit this program.', 'danger')
        return redirect(url_for('programs.index'))
    
    db.session.delete(series)
    db.session.commit()
    
    flash('Series removed from program.', 'success')
    return redirect(url_for('programs.view', program_id=program.id))


# Legacy exercise routes (deprecated but kept for compatibility)
@bp.route('/day/<int:day_id>/exercises/add', methods=['GET', 'POST'])
@login_required
def add_exercise(day_id):
    """Add exercise to program day (legacy - redirects to add_series)"""
    return redirect(url_for('programs.add_series', day_id=day_id))


@bp.route('/exercise/<int:exercise_id>/delete', methods=['POST'])
@login_required
def delete_exercise(exercise_id):
    """Delete exercise from program day (legacy)"""
    program_exercise = ProgramExercise.query.get_or_404(exercise_id)
    series = program_exercise.series
    program = series.day.week.program
    
    # Check permissions
    if program.created_by != current_user.id:
        flash('You do not have permission to edit this program.', 'danger')
        return redirect(url_for('programs.index'))
    
    # If this is the only exercise in the series, delete the series
    if len(series.exercises) == 1:
        db.session.delete(series)
    else:
        db.session.delete(program_exercise)
    
    db.session.commit()
    
    flash('Exercise removed from program.', 'success')
    return redirect(url_for('programs.view', program_id=program.id))


# Program sharing
@bp.route('/<int:program_id>/share', methods=['GET', 'POST'])
@login_required
def share(program_id):
    """Share program with another user"""
    program = Program.query.get_or_404(program_id)
    
    # Check permissions
    if program.created_by != current_user.id:
        flash('You can only share programs you created.', 'danger')
        return redirect(url_for('programs.index'))
    
    form = ProgramShareForm()
    
    # Populate users (exclude self)
    users = User.query.filter(User.id != current_user.id).order_by(User.username).all()
    form.user_id.choices = [(u.id, u.username) for u in users]
    
    if form.validate_on_submit():
        # Check if already shared
        existing = ProgramShare.query.filter_by(
            program_id=program.id,
            shared_with_user_id=form.user_id.data
        ).first()
        
        if existing:
            flash('Program is already shared with this user.', 'warning')
            return redirect(url_for('programs.view', program_id=program.id))
        
        share = ProgramShare(
            program_id=program.id,
            shared_with_user_id=form.user_id.data,
            can_edit=False  # Always read-only for now
        )
        db.session.add(share)
        db.session.commit()
        
        user = User.query.get(form.user_id.data)
        username = user.username if user else 'user'
        flash(f'Program shared with {username}!', 'success')
        return redirect(url_for('programs.view', program_id=program.id))
    
    # Get list of users already shared with
    existing_shares = ProgramShare.query.filter_by(program_id=program.id).all()
    
    return render_template('programs/share.html', form=form, program=program, existing_shares=existing_shares)


@bp.route('/share/<int:share_id>/delete', methods=['POST'])
@login_required
def unshare(share_id):
    """Remove program share"""
    share = ProgramShare.query.get_or_404(share_id)
    program = share.program
    
    # Check permissions
    if program.created_by != current_user.id:
        flash('You can only unshare programs you created.', 'danger')
        return redirect(url_for('programs.index'))
    
    user = share.user
    db.session.delete(share)
    db.session.commit()
    
    flash(f'Program unshared from {user.username}.', 'success')
    return redirect(url_for('programs.view', program_id=program.id))
