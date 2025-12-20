from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import MasterExercise, MasterEquipment, ExerciseEquipmentMapping, UserExercisePreference, ExerciseEquipmentVariation, EquipmentVariation
from app.forms import MasterExerciseForm, UserExercisePreferenceForm
import json

bp = Blueprint('exercises', __name__, url_prefix='/exercises')


@bp.route('/')
@login_required
def index():
    """Exercise library page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    category = request.args.get('category', '', type=str)
    per_page = 20
    
    query = MasterExercise.query
    
    # Search filter
    if search:
        query = query.filter(MasterExercise.name.ilike(f'%{search}%'))
    
    # Category filter
    if category:
        query = query.filter_by(category=category)
    
    query = query.order_by(MasterExercise.name)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Fixed categories list
    categories = ['Strength', 'Cardio', 'Stretch', 'Resistance', 'Bodyweight']
    
    return render_template('exercises/index.html', 
                         exercises=pagination.items, 
                         pagination=pagination,
                         categories=categories,
                         search=search,
                         selected_category=category)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new exercise"""
    form = MasterExerciseForm()
    
    if form.validate_on_submit():
        # Handle secondary muscles as JSON array
        secondary_muscles = [m.strip() for m in form.secondary_muscles.data.split(',')] if form.secondary_muscles.data else []
        
        exercise = MasterExercise(
            name=form.name.data,
            description=form.description.data,
            category=form.category.data,
            primary_muscle=form.primary_muscle.data if form.primary_muscle.data else None,
            secondary_muscles=json.dumps(secondary_muscles),
            difficulty_level=form.difficulty_level.data if form.difficulty_level.data else None,
            created_by=current_user.id
        )
        
        db.session.add(exercise)
        db.session.flush()
        
        # Handle equipment from POST data (added via modal)
        equipment_ids = request.form.getlist('equipment_ids[]')
        for equipment_id in equipment_ids:
            if equipment_id:
                mapping = ExerciseEquipmentMapping(exercise_id=exercise.id, equipment_id=int(equipment_id))
                db.session.add(mapping)
        
        # Handle equipment variations from POST data
        variation_data = request.form.getlist('variations[]')
        for var_json in variation_data:
            if var_json:
                var_dict = json.loads(var_json)
                var = ExerciseEquipmentVariation(
                    exercise_id=exercise.id,
                    equipment_id=var_dict['equipment_id'],
                    variation_id=var_dict['variation_id'],
                    selected_option=var_dict['selected_option']
                )
                db.session.add(var)
        
        db.session.commit()
        
        flash(f'Exercise "{exercise.name}" created successfully!', 'success')
        return redirect(url_for('exercises.index'))
    
    # Get all equipment for modal
    equipment_list = MasterEquipment.query.order_by(MasterEquipment.name).all()
    
    return render_template('exercises/create.html', form=form, equipment_list=equipment_list)


@bp.route('/<int:exercise_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(exercise_id):
    """Edit exercise"""
    exercise = MasterExercise.query.get_or_404(exercise_id)
    
    # Check permissions
    if not current_user.is_admin and exercise.created_by != current_user.id:
        flash('You do not have permission to edit this exercise.', 'danger')
        return redirect(url_for('exercises.index'))
    
    form = MasterExerciseForm()
    
    if form.validate_on_submit():
        # Handle secondary muscles as JSON array
        secondary_muscles = [m.strip() for m in form.secondary_muscles.data.split(',')] if form.secondary_muscles.data else []
        
        exercise.name = form.name.data
        exercise.description = form.description.data
        exercise.category = form.category.data
        exercise.primary_muscle = form.primary_muscle.data if form.primary_muscle.data else None
        exercise.secondary_muscles = json.dumps(secondary_muscles)
        exercise.difficulty_level = form.difficulty_level.data if form.difficulty_level.data else None
        
        # Update equipment mappings
        ExerciseEquipmentMapping.query.filter_by(exercise_id=exercise.id).delete()
        equipment_ids = request.form.getlist('equipment_ids[]')
        for equipment_id in equipment_ids:
            if equipment_id:
                mapping = ExerciseEquipmentMapping(exercise_id=exercise.id, equipment_id=int(equipment_id))
                db.session.add(mapping)
        
        # Update equipment variations
        ExerciseEquipmentVariation.query.filter_by(exercise_id=exercise.id).delete()
        variation_data = request.form.getlist('variations[]')
        for var_json in variation_data:
            if var_json:
                var_dict = json.loads(var_json)
                var = ExerciseEquipmentVariation(
                    exercise_id=exercise.id,
                    equipment_id=var_dict['equipment_id'],
                    variation_id=var_dict['variation_id'],
                    selected_option=var_dict['selected_option']
                )
                db.session.add(var)
        
        db.session.commit()
        flash(f'Exercise "{exercise.name}" updated successfully!', 'success')
        return redirect(url_for('exercises.index'))
    
    elif request.method == 'GET':
        form.name.data = exercise.name
        form.description.data = exercise.description
        form.category.data = exercise.category
        form.primary_muscle.data = exercise.primary_muscle
        
        # Parse JSON arrays back to comma-separated strings
        secondary_muscles = json.loads(exercise.secondary_muscles) if exercise.secondary_muscles else []
        form.secondary_muscles.data = ', '.join(secondary_muscles)
        
        form.difficulty_level.data = exercise.difficulty_level
    
    # Get equipment for modal
    equipment_list = MasterEquipment.query.order_by(MasterEquipment.name).all()
    current_equipment_ids = [e.id for e in exercise.equipment]
    current_variations = ExerciseEquipmentVariation.query.filter_by(exercise_id=exercise.id).all()
    
    return render_template('exercises/edit.html', 
                         form=form, 
                         exercise=exercise,
                         equipment_list=equipment_list,
                         current_equipment_ids=current_equipment_ids,
                         current_variations=current_variations)


@bp.route('/<int:exercise_id>/delete', methods=['POST'])
@login_required
def delete(exercise_id):
    """Delete exercise"""
    exercise = MasterExercise.query.get_or_404(exercise_id)
    
    # Check permissions
    if not current_user.is_admin and exercise.created_by != current_user.id:
        flash('You do not have permission to delete this exercise.', 'danger')
        return redirect(url_for('exercises.index'))
    
    name = exercise.name
    db.session.delete(exercise)
    db.session.commit()
    
    flash(f'Exercise "{name}" deleted successfully.', 'success')
    return redirect(url_for('exercises.index'))


# API endpoints for AJAX
@bp.route('/search')
@login_required
def search():
    """Search exercises (for AJAX)"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    exercises = MasterExercise.query.filter(
        MasterExercise.name.ilike(f'%{query}%')
    ).limit(10).all()
    
    results = []
    for ex in exercises:
        results.append({
            'id': ex.id,
            'name': ex.name,
            'category': ex.category,
            'primary_muscle': ex.primary_muscle,
            'equipment': [{'id': e.id, 'name': e.name} for e in ex.equipment]
        })
    
    return jsonify(results)


@bp.route('/equipment/<int:equipment_id>/variations')
@login_required
def equipment_variations(equipment_id):
    """Get variations for equipment (for AJAX)"""
    equipment = MasterEquipment.query.get_or_404(equipment_id)
    variations = EquipmentVariation.query.filter_by(equipment_id=equipment_id).all()
    
    results = []
    for var in variations:
        options = json.loads(var.options) if var.options else []
        results.append({
            'id': var.id,
            'name': var.name,
            'options': options
        })
    
    return jsonify(results)


# User exercise preferences
@bp.route('/<int:exercise_id>/preference', methods=['GET', 'POST'])
@login_required
def set_preference(exercise_id):
    """Set user preference for an exercise"""
    exercise = MasterExercise.query.get_or_404(exercise_id)
    preference = UserExercisePreference.query.filter_by(
        user_id=current_user.id,
        exercise_id=exercise_id
    ).first()
    
    form = UserExercisePreferenceForm()
    
    if form.validate_on_submit():
        if not preference:
            preference = UserExercisePreference(
                user_id=current_user.id,
                exercise_id=exercise_id
            )
            db.session.add(preference)
        
        preference.rating = form.rating.data
        preference.notes = form.notes.data
        
        db.session.commit()
        flash('Preference saved!', 'success')
        return redirect(url_for('exercises.index'))
    
    elif request.method == 'GET' and preference:
        form.rating.data = preference.rating
        form.notes.data = preference.notes
    
    return render_template('exercises/preference.html', 
                         form=form, 
                         exercise=exercise, 
                         preference=preference)


@bp.route('/api/secondary-muscles')
@login_required
def get_secondary_muscles():
    """Get all unique secondary muscles for autocomplete"""
    exercises = MasterExercise.query.all()
    muscles = set()
    
    for exercise in exercises:
        if exercise.secondary_muscles:
            try:
                secondary_list = json.loads(exercise.secondary_muscles)
                for muscle in secondary_list:
                    if muscle and muscle.strip():
                        muscles.add(muscle.strip())
            except:
                pass
    
    return jsonify(sorted(list(muscles)))
