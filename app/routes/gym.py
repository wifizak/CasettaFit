from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import UserGym, GymEquipment, GymExercise, MasterExercise, MasterEquipment
from app.forms import UserGymForm, GymEquipmentForm, GymExerciseForm
import json

bp = Blueprint('gym', __name__, url_prefix='/gym')


@bp.route('/')
@login_required
def index():
    """List user's gyms"""
    gyms = UserGym.query.filter_by(user_id=current_user.id).order_by(UserGym.name).all()
    return render_template('gym/index.html', gyms=gyms)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new gym"""
    form = UserGymForm()
    
    if form.validate_on_submit():
        gym = UserGym(
            name=form.name.data,
            address=form.address.data,
            picture_url=form.picture_url.data,
            user_id=current_user.id,
            created_by=current_user.id,
            is_shared=form.is_shared.data
        )
        db.session.add(gym)
        db.session.commit()
        
        flash(f'Gym "{gym.name}" created successfully!', 'success')
        return redirect(url_for('gym.view', gym_id=gym.id))
    
    return render_template('gym/create.html', form=form)


@bp.route('/<int:gym_id>')
@login_required
def view(gym_id):
    """View gym details"""
    gym = UserGym.query.get_or_404(gym_id)
    
    # Check permissions
    if gym.user_id != current_user.id and not gym.is_shared:
        flash('You do not have access to this gym.', 'danger')
        return redirect(url_for('gym.index'))
    
    return render_template('gym/view.html', gym=gym)


@bp.route('/<int:gym_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(gym_id):
    """Edit gym"""
    gym = UserGym.query.get_or_404(gym_id)
    
    # Check permissions
    if gym.user_id != current_user.id:
        flash('You do not have permission to edit this gym.', 'danger')
        return redirect(url_for('gym.index'))
    
    form = UserGymForm()
    
    if form.validate_on_submit():
        gym.name = form.name.data
        gym.address = form.address.data
        gym.picture_url = form.picture_url.data
        gym.is_shared = form.is_shared.data
        db.session.commit()
        
        flash(f'Gym "{gym.name}" updated successfully!', 'success')
        return redirect(url_for('gym.view', gym_id=gym.id))
    
    elif request.method == 'GET':
        form.name.data = gym.name
        form.address.data = gym.address
        form.picture_url.data = gym.picture_url
        form.is_shared.data = gym.is_shared
    
    return render_template('gym/edit.html', form=form, gym=gym)


@bp.route('/<int:gym_id>/delete', methods=['POST'])
@login_required
def delete(gym_id):
    """Delete gym"""
    gym = UserGym.query.get_or_404(gym_id)
    
    # Check permissions
    if gym.user_id != current_user.id:
        flash('You do not have permission to delete this gym.', 'danger')
        return redirect(url_for('gym.index'))
    
    name = gym.name
    db.session.delete(gym)
    db.session.commit()
    
    flash(f'Gym "{name}" deleted successfully.', 'success')
    return redirect(url_for('gym.index'))


# Equipment management
@bp.route('/<int:gym_id>/equipment/add', methods=['GET', 'POST'])
@login_required
def add_equipment(gym_id):
    """Add equipment to gym"""
    gym = UserGym.query.get_or_404(gym_id)
    
    # Check permissions
    if gym.user_id != current_user.id:
        flash('You do not have permission to edit this gym.', 'danger')
        return redirect(url_for('gym.index'))
    
    form = GymEquipmentForm()
    
    # Populate equipment choices from MasterEquipment
    equipment_list = MasterEquipment.query.order_by(MasterEquipment.name).all()
    form.equipment_id.choices = [(e.id, e.name) for e in equipment_list]
    
    if form.validate_on_submit():
        # Check if already exists
        existing = GymEquipment.query.filter_by(
            gym_id=gym.id,
            equipment_id=form.equipment_id.data
        ).first()
        
        if existing:
            flash('This equipment is already in your gym.', 'warning')
            return redirect(url_for('gym.view', gym_id=gym.id))
        
        # Parse plate sizes from comma-separated string to JSON
        plate_sizes = None
        if form.plate_sizes.data:
            sizes = [float(s.strip()) for s in form.plate_sizes.data.split(',') if s.strip()]
            plate_sizes = json.dumps(sizes)
        
        equipment = GymEquipment(
            gym_id=gym.id,
            equipment_id=form.equipment_id.data,
            quantity=form.quantity.data or 1,
            progression_type=form.progression_type.data,
            weight_value=form.weight_value.data,
            plate_sizes=plate_sizes,
            stack_increment=form.stack_increment.data,
            notes=form.notes.data
        )
        db.session.add(equipment)
        db.session.commit()
        
        master_eq = MasterEquipment.query.get(form.equipment_id.data)
        flash(f'Equipment "{master_eq.name}" added successfully!', 'success')
        return redirect(url_for('gym.view', gym_id=gym.id))
    
    return render_template('gym/add_equipment.html', form=form, gym=gym)


@bp.route('/equipment/<int:equipment_id>/delete', methods=['POST'])
@login_required
def delete_equipment(equipment_id):
    """Delete equipment"""
    equipment = GymEquipment.query.get_or_404(equipment_id)
    gym = equipment.gym
    
    # Check permissions
    if gym.user_id != current_user.id:
        flash('You do not have permission to edit this gym.', 'danger')
        return redirect(url_for('gym.index'))
    
    gym_id = gym.id
    name = equipment.name
    db.session.delete(equipment)
    db.session.commit()
    
    flash(f'Equipment "{name}" removed successfully.', 'success')
    return redirect(url_for('gym.view', gym_id=gym_id))


# Exercise assignment to gym
@bp.route('/<int:gym_id>/exercises/add', methods=['GET', 'POST'])
@login_required
def add_exercise(gym_id):
    """Add exercise to gym"""
    gym = UserGym.query.get_or_404(gym_id)
    
    # Check permissions
    if gym.user_id != current_user.id:
        flash('You do not have permission to edit this gym.', 'danger')
        return redirect(url_for('gym.index'))
    
    form = GymExerciseForm()
    
    # Populate exercises
    exercises = MasterExercise.query.order_by(MasterExercise.name).all()
    form.exercise_id.choices = [(e.id, e.name) for e in exercises]
    
    if form.validate_on_submit():
        # Check if already exists
        existing = GymExercise.query.filter_by(
            gym_id=gym.id,
            exercise_id=form.exercise_id.data
        ).first()
        
        if existing:
            flash('This exercise is already in your gym.', 'warning')
            return redirect(url_for('gym.view', gym_id=gym.id))
        
        gym_exercise = GymExercise(
            gym_id=gym.id,
            exercise_id=form.exercise_id.data,
            notes=form.notes.data,
            is_favorite=form.is_favorite.data
        )
        db.session.add(gym_exercise)
        db.session.commit()
        
        flash('Exercise added to gym successfully!', 'success')
        return redirect(url_for('gym.view', gym_id=gym.id))
    
    return render_template('gym/add_exercise.html', form=form, gym=gym)


@bp.route('/exercises/<int:gym_exercise_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_exercise(gym_exercise_id):
    """Edit gym exercise configuration"""
    gym_exercise = GymExercise.query.get_or_404(gym_exercise_id)
    gym = gym_exercise.gym
    
    # Check permissions
    if gym.user_id != current_user.id:
        flash('You do not have permission to edit this gym.', 'danger')
        return redirect(url_for('gym.index'))
    
    form = GymExerciseForm()
    
    # Populate exercises
    exercises = MasterExercise.query.order_by(MasterExercise.name).all()
    form.exercise_id.choices = [(e.id, e.name) for e in exercises]
    
    if form.validate_on_submit():
        gym_exercise.exercise_id = form.exercise_id.data
        gym_exercise.notes = form.notes.data
        gym_exercise.is_favorite = form.is_favorite.data
        db.session.commit()
        
        flash('Exercise configuration updated successfully!', 'success')
        return redirect(url_for('gym.view', gym_id=gym.id))
    
    elif request.method == 'GET':
        form.exercise_id.data = gym_exercise.exercise_id
        form.notes.data = gym_exercise.notes
        form.is_favorite.data = gym_exercise.is_favorite
    
    return render_template('gym/edit_exercise.html', form=form, gym_exercise=gym_exercise, gym=gym)


@bp.route('/exercises/<int:gym_exercise_id>/delete', methods=['POST'])
@login_required
def delete_exercise(gym_exercise_id):
    """Remove exercise from gym"""
    gym_exercise = GymExercise.query.get_or_404(gym_exercise_id)
    gym = gym_exercise.gym
    
    # Check permissions
    if gym.user_id != current_user.id:
        flash('You do not have permission to edit this gym.', 'danger')
        return redirect(url_for('gym.index'))
    
    gym_id = gym.id
    db.session.delete(gym_exercise)
    db.session.commit()
    
    flash('Exercise removed from gym successfully.', 'success')
    return redirect(url_for('gym.view', gym_id=gym_id))
