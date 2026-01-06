from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import MasterEquipment, EquipmentVariation, UserGym, sync_gym_exercise_associations
from app.forms import MasterEquipmentForm, EquipmentVariationForm
from sqlalchemy import desc
import json

bp = Blueprint('equipment', __name__, url_prefix='/equipment')


@bp.route('/')
@login_required
def index():
    """Equipment library page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    equipment_type = request.args.get('type', '', type=str)
    sort_by = request.args.get('sort_by', 'name', type=str)
    sort_dir = request.args.get('sort_dir', 'asc', type=str)
    per_page = 20
    
    query = MasterEquipment.query
    
    # Search filter - search across name and description
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                MasterEquipment.name.ilike(search_filter),
                MasterEquipment.description.ilike(search_filter),
                MasterEquipment.equipment_type.ilike(search_filter)
            )
        )
    
    # Type filter
    if equipment_type:
        query = query.filter_by(equipment_type=equipment_type)
    
    # Sorting
    valid_sort_fields = {
        'name': MasterEquipment.name,
        'equipment_type': MasterEquipment.equipment_type,
        'created_at': MasterEquipment.created_at
    }
    
    sort_field = valid_sort_fields.get(sort_by, MasterEquipment.name)
    if sort_dir == 'desc':
        sort_field = desc(sort_field)
    
    query = query.order_by(sort_field)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Equipment types list
    equipment_types = ['Strength', 'Cardio', 'Body', 'Resistance']
    
    return render_template('equipment/index.html', 
                         equipment_list=pagination.items, 
                         pagination=pagination,
                         search=search,
                         selected_type=equipment_type,
                         equipment_types=equipment_types,
                         sort_by=sort_by,
                         sort_dir=sort_dir)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new equipment"""
    form = MasterEquipmentForm()
    
    if form.validate_on_submit():
        equipment = MasterEquipment(
            name=form.name.data,
            description=form.description.data,
            manufacturer=form.manufacturer.data if form.manufacturer.data else None,
            model=form.model.data if form.model.data else None,
            equipment_type=form.equipment_type.data,
            created_by=current_user.id
        )
        
        db.session.add(equipment)
        db.session.flush()
        
        # Handle variations during creation
        variation_names = request.form.getlist('variation_names[]')
        variation_options = request.form.getlist('variation_options[]')
        
        for name, options_text in zip(variation_names, variation_options):
            if name and options_text:
                # Parse options from textarea (one per line) to JSON
                options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
                if options:  # Only create if there are valid options
                    variation = EquipmentVariation(
                        equipment_id=equipment.id,
                        name=name.strip(),
                        options=json.dumps(options)
                    )
                    db.session.add(variation)
        
        # Handle gym associations
        gym_ids = request.form.getlist('gym_ids[]')
        affected_gym_ids = []
        for gym_id in gym_ids:
            if gym_id:
                try:
                    gym = db.session.get(UserGym, int(gym_id))
                    if gym:
                        equipment.gyms.append(gym)
                        affected_gym_ids.append(int(gym_id))
                except ValueError:
                    continue  # Skip invalid gym_id
        
        db.session.commit()
        
        # Auto-associate exercises with gyms that now have this equipment
        for gym_id in affected_gym_ids:
            sync_gym_exercise_associations(gym_id)
        db.session.commit()
        
        flash(f'Equipment "{equipment.name}" created successfully!', 'success')
        return redirect(url_for('equipment.index'))
    
    # Get all gyms for current user
    gyms = UserGym.query.filter_by(user_id=current_user.id).order_by(UserGym.name).all()
    
    # Get distinct manufacturers and models for autocomplete
    manufacturers = db.session.query(MasterEquipment.manufacturer).filter(
        MasterEquipment.manufacturer.isnot(None),
        MasterEquipment.manufacturer != ''
    ).distinct().order_by(MasterEquipment.manufacturer).all()
    manufacturers = [m[0] for m in manufacturers]
    
    models = db.session.query(MasterEquipment.model).filter(
        MasterEquipment.model.isnot(None),
        MasterEquipment.model != ''
    ).distinct().order_by(MasterEquipment.model).all()
    models = [m[0] for m in models]
    
    return render_template('equipment/create.html', form=form, gyms=gyms, 
                         manufacturers=manufacturers, models=models)


@bp.route('/<int:equipment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(equipment_id):
    """Edit equipment"""
    equipment = MasterEquipment.query.get_or_404(equipment_id)
    
    # Check permissions
    if not current_user.is_admin and equipment.created_by != current_user.id:
        flash('You do not have permission to edit this equipment.', 'danger')
        return redirect(url_for('equipment.index'))
    
    form = MasterEquipmentForm()
    
    if form.validate_on_submit():
        equipment.name = form.name.data
        equipment.description = form.description.data
        equipment.manufacturer = form.manufacturer.data if form.manufacturer.data else None
        equipment.model = form.model.data if form.model.data else None
        equipment.equipment_type = form.equipment_type.data
        
        # Track old gym associations
        old_gym_ids = set([g.id for g in equipment.gyms])
        
        # Update gym associations
        equipment.gyms.clear()
        gym_ids = request.form.getlist('gym_ids[]')
        new_gym_ids = set()
        for gym_id in gym_ids:
            if gym_id:
                try:
                    gym = db.session.get(UserGym, int(gym_id))
                    if gym:
                        equipment.gyms.append(gym)
                        new_gym_ids.add(int(gym_id))
                except ValueError:
                    continue  # Skip invalid gym_id
        
        db.session.commit()
        
        # Sync exercises for all affected gyms (both added and removed)
        affected_gym_ids = old_gym_ids.union(new_gym_ids)
        for gym_id in affected_gym_ids:
            sync_gym_exercise_associations(gym_id)
        db.session.commit()
        
        flash(f'Equipment "{equipment.name}" updated successfully!', 'success')
        return redirect(url_for('equipment.index'))
    
    elif request.method == 'GET':
        form.name.data = equipment.name
        form.description.data = equipment.description
        form.manufacturer.data = equipment.manufacturer
        form.model.data = equipment.model
        form.equipment_type.data = equipment.equipment_type
    
    # Get all unique variation types from database for suggestions
    from app.models import EquipmentVariation
    existing_variations = db.session.query(
        EquipmentVariation.name,
        EquipmentVariation.options
    ).distinct().all()
    
    # Convert to list of dicts for template
    variation_templates = []
    seen = set()
    for var in existing_variations:
        if var.name not in seen:
            variation_templates.append({
                'name': var.name,
                'options': var.options
            })
            seen.add(var.name)
    
    # Get all gyms for current user
    gyms = UserGym.query.filter_by(user_id=current_user.id).order_by(UserGym.name).all()
    current_gym_ids = [g.id for g in equipment.gyms]
    
    # Get distinct manufacturers and models for autocomplete
    manufacturers = db.session.query(MasterEquipment.manufacturer).filter(
        MasterEquipment.manufacturer.isnot(None),
        MasterEquipment.manufacturer != ''
    ).distinct().order_by(MasterEquipment.manufacturer).all()
    manufacturers = [m[0] for m in manufacturers]
    
    models = db.session.query(MasterEquipment.model).filter(
        MasterEquipment.model.isnot(None),
        MasterEquipment.model != ''
    ).distinct().order_by(MasterEquipment.model).all()
    models = [m[0] for m in models]
    
    return render_template('equipment/edit.html', form=form, equipment=equipment, 
                         variation_templates=variation_templates, gyms=gyms, current_gym_ids=current_gym_ids,
                         manufacturers=manufacturers, models=models)


@bp.route('/<int:equipment_id>/delete', methods=['POST'])
@login_required
def delete(equipment_id):
    """Delete equipment"""
    equipment = MasterEquipment.query.get_or_404(equipment_id)
    
    # Check permissions
    if not current_user.is_admin and equipment.created_by != current_user.id:
        flash('You do not have permission to delete this equipment.', 'danger')
        return redirect(url_for('equipment.index'))
    
    name = equipment.name
    db.session.delete(equipment)
    db.session.commit()
    
    flash(f'Equipment "{name}" deleted successfully.', 'success')
    return redirect(url_for('equipment.index'))


# Variation management
@bp.route('/<int:equipment_id>/variations/add', methods=['GET', 'POST'])
@login_required
def add_variation(equipment_id):
    """Add variation to equipment"""
    equipment = MasterEquipment.query.get_or_404(equipment_id)
    
    # Check permissions
    if not current_user.is_admin and equipment.created_by != current_user.id:
        flash('You do not have permission to edit this equipment.', 'danger')
        return redirect(url_for('equipment.index'))
    
    if request.method == 'POST':
        # Handle direct POST from modal
        name = request.form.get('name', '').strip()
        options_text = request.form.get('options', '').strip()
        
        if name and options_text:
            # Parse options from textarea (one per line) to JSON
            options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
            
            variation = EquipmentVariation(
                equipment_id=equipment.id,
                name=name,
                options=json.dumps(options)
            )
            
            db.session.add(variation)
            db.session.commit()
            
            flash(f'Variation "{variation.name}" added successfully!', 'success')
            return redirect(url_for('equipment.edit', equipment_id=equipment.id))
        else:
            flash('Please provide both variation name and options.', 'danger')
            return redirect(url_for('equipment.edit', equipment_id=equipment.id))
    
    # GET request - render standalone form (optional)
    form = EquipmentVariationForm()
    return render_template('equipment/add_variation.html', form=form, equipment=equipment)


@bp.route('/variations/<int:variation_id>/delete', methods=['POST'])
@login_required
def delete_variation(variation_id):
    """Delete variation"""
    variation = EquipmentVariation.query.get_or_404(variation_id)
    equipment = variation.equipment
    
    # Check permissions
    if not current_user.is_admin and equipment.created_by != current_user.id:
        flash('You do not have permission to edit this equipment.', 'danger')
        return redirect(url_for('equipment.index'))
    
    db.session.delete(variation)
    db.session.commit()
    
    flash('Variation deleted successfully.', 'success')
    return redirect(url_for('equipment.edit', equipment_id=equipment.id))


@bp.route('/api/manufacturers')
@login_required
def get_manufacturers():
    """API endpoint to get list of manufacturers for autocomplete"""
    manufacturers = db.session.query(MasterEquipment.manufacturer).filter(
        MasterEquipment.manufacturer.isnot(None),
        MasterEquipment.manufacturer != ''
    ).distinct().order_by(MasterEquipment.manufacturer).all()
    return jsonify([m[0] for m in manufacturers])


@bp.route('/api/models')
@login_required
def get_models():
    """API endpoint to get list of models for autocomplete"""
    models = db.session.query(MasterEquipment.model).filter(
        MasterEquipment.model.isnot(None),
        MasterEquipment.model != ''
    ).distinct().order_by(MasterEquipment.model).all()
    return jsonify([m[0] for m in models])
