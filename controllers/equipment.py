from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import Equipment
from forms import EquipmentForm

equipment_bp = Blueprint('equipment', __name__, url_prefix='/equipment')

@equipment_bp.route('/')
@login_required
def index():
    """Display list of all equipment"""
    equipment_list = Equipment.query.all()
    return render_template('equipment/index.html', equipment_list=equipment_list)

@equipment_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add new equipment"""
    # Check if user is admin or supervisor
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Access denied. You do not have permission to add equipment.', 'danger')
        return redirect(url_for('equipment.index'))
    
    form = EquipmentForm()
    if form.validate_on_submit():
        equipment = Equipment(
            identification_number=form.identification_number.data,
            model=form.model.data,
            manufacturer=form.manufacturer.data,
            power=form.power.data,
            installation_date=form.installation_date.data,
            location_building=form.location_building.data,
            location_floor=form.location_floor.data,
            location_room=form.location_room.data,
            location_details=form.location_details.data,
            serial_number=form.serial_number.data,
            warranty_end_date=form.warranty_end_date.data,
            status=form.status.data,
            notes=form.notes.data
        )
        
        db.session.add(equipment)
        try:
            db.session.commit()
            flash(f'Equipment {form.identification_number.data} has been added!', 'success')
            return redirect(url_for('equipment.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding equipment: {str(e)}', 'danger')
    
    return render_template('equipment/add.html', form=form)

@equipment_bp.route('/<int:equipment_id>', methods=['GET'])
@login_required
def view(equipment_id):
    """View equipment details"""
    equipment = Equipment.query.get_or_404(equipment_id)
    return render_template('equipment/view.html', equipment=equipment)

@equipment_bp.route('/<int:equipment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(equipment_id):
    """Edit equipment details"""
    # Check if user is admin or supervisor
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Access denied. You do not have permission to edit equipment.', 'danger')
        return redirect(url_for('equipment.index'))
    
    equipment = Equipment.query.get_or_404(equipment_id)
    form = EquipmentForm(obj=equipment)
    
    if form.validate_on_submit():
        equipment.identification_number = form.identification_number.data
        equipment.model = form.model.data
        equipment.manufacturer = form.manufacturer.data
        equipment.power = form.power.data
        equipment.installation_date = form.installation_date.data
        equipment.location_building = form.location_building.data
        equipment.location_floor = form.location_floor.data
        equipment.location_room = form.location_room.data
        equipment.location_details = form.location_details.data
        equipment.serial_number = form.serial_number.data
        equipment.warranty_end_date = form.warranty_end_date.data
        equipment.status = form.status.data
        equipment.notes = form.notes.data
        
        try:
            db.session.commit()
            flash(f'Equipment {equipment.identification_number} has been updated!', 'success')
            return redirect(url_for('equipment.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating equipment: {str(e)}', 'danger')
    
    return render_template('equipment/edit.html', form=form, equipment=equipment)

@equipment_bp.route('/<int:equipment_id>/delete', methods=['POST'])
@login_required
def delete(equipment_id):
    """Delete equipment"""
    # Check if user is admin
    if not current_user.is_admin():
        flash('Access denied. Only administrators can delete equipment.', 'danger')
        return redirect(url_for('equipment.index'))
    
    equipment = Equipment.query.get_or_404(equipment_id)
    
    try:
        db.session.delete(equipment)
        db.session.commit()
        flash(f'Equipment {equipment.identification_number} has been deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting equipment: {str(e)}', 'danger')
    
    return redirect(url_for('equipment.index'))
