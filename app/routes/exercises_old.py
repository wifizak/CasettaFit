from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import MasterExercise, ExerciseCategory, ExerciseCategoryMapping, MasterEquipment, ExerciseEquipmentMapping, UserExercisePreference
from app.forms import MasterExerciseForm, ExerciseCategoryForm, UserExercisePreferenceForm
import json

bp = Blueprint('exercises', __name__, url_prefix='/exercises')


@bp.route('/')
@login_required
def index():
    """Exercise library page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    category_id = request.args.get('category', type=int)
    per_page = 20
    
    query = MasterExercise.query
    
    # Search filter
    if search:
        query = query.filter(MasterExercise.name.ilike(f'%{search}%'))
    
    # Category filter
    if category_id:
        query = query.join(ExerciseCategoryMapping).filter(ExerciseCategoryMapping.category_id == category_id)
    
    query = query.order_by(MasterExercise.name)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    categories = ExerciseCategory.query.order_by(ExerciseCategory.name).all()
    
    return render_template('exercises/index.html', 
                         exercises=pagination.items, 
                         pagination=pagination,
                         categories=categories,
                         search=search,
                         selected_category=category_id)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new exercise"""
    form = MasterExerciseForm()
    
    # Populate categories and equipment
    categories = ExerciseCategory.query.order_by(ExerciseCategory.name).all()
    form.categories.choices = [(c.id, c.name) for c in categories]
    
    equipment_list = MasterEquipment.query.order_by(MasterEquipment.name).all()
    form.equipment.choices = [(e.id, e.name) for e in equipment_list]
    
    if form.validate_on_submit():
        # Handle secondary muscles and sub-muscle groups as JSON arrays
        secondary_muscles = [m.strip() for m in form.secondary_muscles.data.split(',')] if form.secondary_muscles.data else []
        sub_muscle_groups = [m.strip() for m in form.sub_muscle_groups.data.split(',')] if form.sub_muscle_groups.data else []
        
        exercise = MasterExercise(
            name=form.name.data,
            description=form.description.data,
            primary_muscle=form.primary_muscle.data if form.primary_muscle.data else None,
            secondary_muscles=json.dumps(secondary_muscles),
            sub_muscle_groups=json.dumps(sub_muscle_groups),
            difficulty_level=form.difficulty_level.data if form.difficulty_level.data else None,
            suggested_sets=form.suggested_sets.data,
            suggested_reps=form.suggested_reps.data,
            suggested_dropset=form.suggested_dropset.data,
            created_by=current_user.id
        )
        
        db.session.add(exercise)
        db.session.flush()
        
        # Add category mappings
        for category_id in form.categories.data:
            mapping = ExerciseCategoryMapping(exercise_id=exercise.id, category_id=category_id)
            db.session.add(mapping)
        
        # Add equipment mappings
        for equipment_id in form.equipment.data:
            mapping = ExerciseEquipmentMapping(exercise_id=exercise.id, equipment_id=equipment_id)
            db.session.add(mapping)
        
        db.session.commit()
        
        flash(f'Exercise "{exercise.name}" created successfully!', 'success')
        return redirect(url_for('exercises.index'))
    
    return render_template('exercises/create.html', form=form)


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
    
    # Populate categories and equipment
    categories = ExerciseCategory.query.order_by(ExerciseCategory.name).all()
    form.categories.choices = [(c.id, c.name) for c in categories]
    
    equipment_list = MasterEquipment.query.order_by(MasterEquipment.name).all()
    form.equipment.choices = [(e.id, e.name) for e in equipment_list]
    
    if form.validate_on_submit():
        # Handle secondary muscles and sub-muscle groups as JSON arrays
        secondary_muscles = [m.strip() for m in form.secondary_muscles.data.split(',')] if form.secondary_muscles.data else []
        sub_muscle_groups = [m.strip() for m in form.sub_muscle_groups.data.split(',')] if form.sub_muscle_groups.data else []
        
        exercise.name = form.name.data
        exercise.description = form.description.data
        exercise.primary_muscle = form.primary_muscle.data if form.primary_muscle.data else None
        exercise.secondary_muscles = json.dumps(secondary_muscles)
        exercise.sub_muscle_groups = json.dumps(sub_muscle_groups)
        exercise.difficulty_level = form.difficulty_level.data if form.difficulty_level.data else None
        exercise.suggested_sets = form.suggested_sets.data
        exercise.suggested_reps = form.suggested_reps.data
        exercise.suggested_dropset = form.suggested_dropset.data
        
        # Update categories
        ExerciseCategoryMapping.query.filter_by(exercise_id=exercise.id).delete()
        for category_id in form.categories.data:
            mapping = ExerciseCategoryMapping(exercise_id=exercise.id, category_id=category_id)
            db.session.add(mapping)
        
        # Update equipment
        ExerciseEquipmentMapping.query.filter_by(exercise_id=exercise.id).delete()
        for equipment_id in form.equipment.data:
            mapping = ExerciseEquipmentMapping(exercise_id=exercise.id, equipment_id=equipment_id)
            db.session.add(mapping)
        
        db.session.commit()
        flash(f'Exercise "{exercise.name}" updated successfully!', 'success')
        return redirect(url_for('exercises.index'))
    
    elif request.method == 'GET':
        form.name.data = exercise.name
        form.description.data = exercise.description
        form.primary_muscle.data = exercise.primary_muscle
        
        # Parse JSON arrays
        secondary_muscles = json.loads(exercise.secondary_muscles) if exercise.secondary_muscles else []
        form.secondary_muscles.data = ', '.join(secondary_muscles)
        
        sub_muscles = json.loads(exercise.sub_muscle_groups) if exercise.sub_muscle_groups else []
        form.sub_muscle_groups.data = ', '.join(sub_muscles)
        
        form.difficulty_level.data = exercise.difficulty_level
        form.suggested_sets.data = exercise.suggested_sets
        form.suggested_reps.data = exercise.suggested_reps
        form.suggested_dropset.data = exercise.suggested_dropset
        form.categories.data = [c.id for c in exercise.categories]
        form.equipment.data = [e.id for e in exercise.equipment]
    
    return render_template('exercises/edit.html', form=form, exercise=exercise)


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


@bp.route('/search')
@login_required
def search():
    """AJAX search for exercises (for modal)"""
    query = request.args.get('q', '', type=str)
    limit = request.args.get('limit', 10, type=int)
    
    if not query:
        return jsonify([])
    
    exercises = MasterExercise.query.filter(
        MasterExercise.name.ilike(f'%{query}%')
    ).limit(limit).all()
    
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'description': e.description,
        'primary_muscle': e.primary_muscle,
        'equipment': [eq.name for eq in e.equipment]
    } for e in exercises])


# Category management routes
@bp.route('/categories')
@login_required
def categories():
    """Manage exercise categories"""
    user_categories = ExerciseCategory.query.filter_by(user_id=current_user.id).order_by(ExerciseCategory.name).all()
    shared_categories = ExerciseCategory.query.filter_by(user_id=None).order_by(ExerciseCategory.name).all()
    
    return render_template('exercises/categories.html', 
                         user_categories=user_categories,
                         shared_categories=shared_categories)


@bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
def create_category():
    """Create new category"""
    form = ExerciseCategoryForm()
    
    if form.validate_on_submit():
        category = ExerciseCategory(
            name=form.name.data,
            user_id=current_user.id
        )
        db.session.add(category)
        db.session.commit()
        
        flash(f'Category "{category.name}" created successfully!', 'success')
        return redirect(url_for('exercises.categories'))
    
    return render_template('exercises/create_category.html', form=form)


@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """Delete category"""
    category = ExerciseCategory.query.get_or_404(category_id)
    
    # Check permissions
    if category.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this category.', 'danger')
        return redirect(url_for('exercises.categories'))
    
    name = category.name
    db.session.delete(category)
    db.session.commit()
    
    flash(f'Category "{name}" deleted successfully.', 'success')
    return redirect(url_for('exercises.categories'))
