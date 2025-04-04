from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from models import Equipment, MaintenancePlan, ChecklistTemplate, ChecklistItem
from models import MaintenanceSchedule, MaintenanceRecord, ChecklistResult, Notification, User
from forms import MaintenancePlanForm, ChecklistTemplateForm, MaintenanceScheduleForm, MaintenanceRecordForm

maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')

@maintenance_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard view"""
    # Get upcoming scheduled maintenance for the next 7 days
    today = datetime.utcnow()
    next_week = today + timedelta(days=7)
    
    if current_user.is_admin() or current_user.is_supervisor():
        # Show all scheduled maintenance
        upcoming_maintenance = MaintenanceSchedule.query.filter(
            MaintenanceSchedule.scheduled_date >= today,
            MaintenanceSchedule.scheduled_date <= next_week,
            MaintenanceSchedule.status == 'scheduled'
        ).order_by(MaintenanceSchedule.scheduled_date).all()
    else:
        # Show only maintenance assigned to this technician
        # First get all notifications for this user
        notifications = Notification.query.filter_by(user_id=current_user.id).all()
        schedule_ids = [n.schedule_id for n in notifications if n.schedule_id]
        
        upcoming_maintenance = MaintenanceSchedule.query.filter(
            MaintenanceSchedule.id.in_(schedule_ids),
            MaintenanceSchedule.scheduled_date >= today,
            MaintenanceSchedule.scheduled_date <= next_week,
            MaintenanceSchedule.status == 'scheduled'
        ).order_by(MaintenanceSchedule.scheduled_date).all()
    
    # Get recent maintenance records
    if current_user.is_admin() or current_user.is_supervisor():
        recent_records = MaintenanceRecord.query.order_by(
            MaintenanceRecord.start_time.desc()
        ).limit(5).all()
    else:
        recent_records = MaintenanceRecord.query.filter_by(
            technician_id=current_user.id
        ).order_by(
            MaintenanceRecord.start_time.desc()
        ).limit(5).all()
    
    # Get unread notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        read=False
    ).order_by(Notification.created_at.desc()).all()
    
    return render_template(
        'dashboard.html',
        upcoming_maintenance=upcoming_maintenance,
        recent_records=recent_records,
        notifications=notifications
    )

# === Maintenance Plans ===

@maintenance_bp.route('/plans')
@login_required
def plans():
    """Display all maintenance plans"""
    plans = MaintenancePlan.query.all()
    return render_template('maintenance/index.html', plans=plans)

@maintenance_bp.route('/plans/add', methods=['GET', 'POST'])
@login_required
def add_plan():
    """Add a new maintenance plan"""
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Access denied. You do not have permission to add maintenance plans.', 'danger')
        return redirect(url_for('maintenance.plans'))
    
    form = MaintenancePlanForm()
    # Populate equipment choices
    form.equipment_id.choices = [(e.id, f"{e.identification_number} - {e.model}") 
                                for e in Equipment.query.all()]
    
    if form.validate_on_submit():
        plan = MaintenancePlan(
            equipment_id=form.equipment_id.data,
            name=form.name.data,
            description=form.description.data,
            frequency_days=form.frequency_days.data,
            is_active=form.is_active.data
        )
        
        db.session.add(plan)
        db.session.commit()
        flash(f'Maintenance plan "{form.name.data}" has been created!', 'success')
        return redirect(url_for('maintenance.plans'))
    
    return render_template('maintenance/add.html', form=form)

@maintenance_bp.route('/plans/<int:plan_id>', methods=['GET'])
@login_required
def view_plan(plan_id):
    """View maintenance plan details"""
    plan = MaintenancePlan.query.get_or_404(plan_id)
    return render_template('maintenance/view.html', plan=plan)

@maintenance_bp.route('/plans/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_plan(plan_id):
    """Edit a maintenance plan"""
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Access denied. You do not have permission to edit maintenance plans.', 'danger')
        return redirect(url_for('maintenance.plans'))
    
    plan = MaintenancePlan.query.get_or_404(plan_id)
    form = MaintenancePlanForm(obj=plan)
    form.equipment_id.choices = [(e.id, f"{e.identification_number} - {e.model}") 
                                for e in Equipment.query.all()]
    
    if form.validate_on_submit():
        plan.equipment_id = form.equipment_id.data
        plan.name = form.name.data
        plan.description = form.description.data
        plan.frequency_days = form.frequency_days.data
        plan.is_active = form.is_active.data
        
        db.session.commit()
        flash(f'Maintenance plan "{plan.name}" has been updated!', 'success')
        return redirect(url_for('maintenance.plans'))
    
    return render_template('maintenance/edit.html', form=form, plan=plan)

@maintenance_bp.route('/plans/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_plan(plan_id):
    """Delete a maintenance plan"""
    if not current_user.is_admin():
        flash('Access denied. Only administrators can delete maintenance plans.', 'danger')
        return redirect(url_for('maintenance.plans'))
    
    plan = MaintenancePlan.query.get_or_404(plan_id)
    
    try:
        db.session.delete(plan)
        db.session.commit()
        flash(f'Maintenance plan "{plan.name}" has been deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting plan: {str(e)}', 'danger')
    
    return redirect(url_for('maintenance.plans'))

# === Checklists ===

@maintenance_bp.route('/checklists')
@login_required
def checklists():
    """Display all checklist templates"""
    templates = ChecklistTemplate.query.all()
    return render_template('maintenance/checklists.html', templates=templates)

@maintenance_bp.route('/checklists/add', methods=['GET', 'POST'])
@login_required
def add_checklist():
    """Add a new checklist template"""
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Access denied. You do not have permission to add checklists.', 'danger')
        return redirect(url_for('maintenance.checklists'))
    
    form = ChecklistTemplateForm()
    form.maintenance_plan_id.choices = [(p.id, p.name) for p in MaintenancePlan.query.all()]
    
    if request.method == 'POST':
        
        # Otherwise, handle form submission    
        if form.validate_on_submit():
            # Print form data for debugging
            print(f"Form validated with {len(form.items.data)} items")
            for i, item in enumerate(form.items.data):
                print(f"Item {i}: {item}")
            
            checklist = ChecklistTemplate(
                maintenance_plan_id=form.maintenance_plan_id.data,
                name=form.name.data,
                description=form.description.data
            )
            
            db.session.add(checklist)
            db.session.commit()
            
            # Now add checklist items
            for i, item_form in enumerate(form.items):
                print(f"Processing item {i}: {item_form.description.data}")
                item = ChecklistItem(
                    template_id=checklist.id,
                    description=item_form.description.data,
                    is_required=item_form.is_required.data,
                    order=i+1
                )
                db.session.add(item)
            
            db.session.commit()
            flash(f'Modelo de checklist "{form.name.data}" foi criado com sucesso!', 'success')
            return redirect(url_for('maintenance.checklists'))
        else:
            # Print validation errors
            print(f"Form validation failed: {form.errors}")
    
    # Ensure at least one item is available
    if len(form.items) < 1:
        form.items.append_entry()
    
    return render_template('maintenance/add_checklist.html', form=form)

@maintenance_bp.route('/checklists/<int:checklist_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_checklist(checklist_id):
    """Edit a checklist template"""
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Access denied. You do not have permission to edit checklists.', 'danger')
        return redirect(url_for('maintenance.checklists'))
    
    checklist = ChecklistTemplate.query.get_or_404(checklist_id)
    form = ChecklistTemplateForm(obj=checklist)
    form.maintenance_plan_id.choices = [(p.id, p.name) for p in MaintenancePlan.query.all()]
    
    # Pre-populate items
    if request.method == 'GET':
        form.items.pop_entry()  # Remove the default empty entry
        for item in ChecklistItem.query.filter_by(template_id=checklist.id).order_by(ChecklistItem.order):
            form.items.append_entry({
                'description': item.description,
                'is_required': item.is_required,
                'order': item.order
            })
    
    if form.validate_on_submit():
        checklist.maintenance_plan_id = form.maintenance_plan_id.data
        checklist.name = form.name.data
        checklist.description = form.description.data
        
        # Delete existing items
        ChecklistItem.query.filter_by(template_id=checklist.id).delete()
        
        # Add updated items
        for i, item_form in enumerate(form.items):
            item = ChecklistItem(
                template_id=checklist.id,
                description=item_form.description.data,
                is_required=item_form.is_required.data,
                order=i+1
            )
            db.session.add(item)
        
        db.session.commit()
        flash(f'Modelo de checklist "{checklist.name}" foi atualizado com sucesso!', 'success')
        return redirect(url_for('maintenance.checklists'))
    
    return render_template('maintenance/edit_checklist.html', form=form, checklist=checklist)

@maintenance_bp.route('/checklists/<int:checklist_id>/delete', methods=['POST'])
@login_required
def delete_checklist(checklist_id):
    """Delete a checklist template"""
    if not current_user.is_admin():
        flash('Access denied. Only administrators can delete checklists.', 'danger')
        return redirect(url_for('maintenance.checklists'))
    
    checklist = ChecklistTemplate.query.get_or_404(checklist_id)
    
    try:
        # Delete all associated items first
        ChecklistItem.query.filter_by(template_id=checklist.id).delete()
        db.session.delete(checklist)
        db.session.commit()
        flash(f'Modelo de checklist "{checklist.name}" foi excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting checklist: {str(e)}', 'danger')
    
    return redirect(url_for('maintenance.checklists'))

# === Scheduling ===

@maintenance_bp.route('/schedule')
@login_required
def schedule_list():
    """Display all scheduled maintenance"""
    if current_user.is_admin() or current_user.is_supervisor():
        schedules = MaintenanceSchedule.query.order_by(MaintenanceSchedule.scheduled_date.desc()).all()
    else:
        # Get schedules assigned to this technician via notifications
        notifications = Notification.query.filter_by(user_id=current_user.id).all()
        schedule_ids = [n.schedule_id for n in notifications if n.schedule_id]
        schedules = MaintenanceSchedule.query.filter(MaintenanceSchedule.id.in_(schedule_ids)).order_by(
            MaintenanceSchedule.scheduled_date.desc()
        ).all()
    
    return render_template('maintenance/schedule_list.html', schedules=schedules)

@maintenance_bp.route('/schedule/add', methods=['GET', 'POST'])
@login_required
def add_schedule():
    """Add a new maintenance schedule"""
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Access denied. You do not have permission to schedule maintenance.', 'danger')
        return redirect(url_for('maintenance.schedule_list'))
    
    form = MaintenanceScheduleForm()
    form.equipment_id.choices = [(e.id, f"{e.identification_number} - {e.model}") 
                                for e in Equipment.query.all()]
    
    # Initially the plan choices will be empty - we'll populate via AJAX
    form.maintenance_plan_id.choices = []
    
    if form.validate_on_submit():
        schedule = MaintenanceSchedule(
            equipment_id=form.equipment_id.data,
            maintenance_plan_id=form.maintenance_plan_id.data,
            scheduled_date=form.scheduled_date.data,
            notes=form.notes.data,
            status='scheduled'
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        # Assign technicians and create notifications
        equipment = Equipment.query.get(form.equipment_id.data)
        plan = MaintenancePlan.query.get(form.maintenance_plan_id.data)
        
        # Get all technicians
        technicians = User.query.filter_by(role='technician').all()
        
        # Create notification for each technician
        for tech in technicians:
            notification = Notification(
                user_id=tech.id,
                schedule_id=schedule.id,
                title='Nova Manutenção Agendada',
                message=f'Manutenção para {equipment.identification_number} ({equipment.model}) '
                        f'foi agendada para {form.scheduled_date.data.strftime("%Y-%m-%d %H:%M")}.'
            )
            db.session.add(notification)
        
        db.session.commit()
        flash('Manutenção foi agendada e os técnicos foram notificados!', 'success')
        return redirect(url_for('maintenance.schedule_list'))
    
    return render_template('maintenance/add_schedule.html', form=form)

@maintenance_bp.route('/schedule/<int:schedule_id>', methods=['GET'])
@login_required
def view_schedule(schedule_id):
    """View scheduled maintenance details"""
    schedule = MaintenanceSchedule.query.get_or_404(schedule_id)
    
    # Mark any notifications for this schedule as read
    if not (current_user.is_admin() or current_user.is_supervisor()):
        notifications = Notification.query.filter_by(
            user_id=current_user.id,
            schedule_id=schedule.id,
            read=False
        ).all()
        
        for notification in notifications:
            notification.read = True
        
        db.session.commit()
    
    return render_template('maintenance/view_schedule.html', schedule=schedule)

@maintenance_bp.route('/schedule/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_schedule(schedule_id):
    """Edit scheduled maintenance"""
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Acesso negado. Você não tem permissão para editar agendamentos.', 'danger')
        return redirect(url_for('maintenance.schedule_list'))
    
    schedule = MaintenanceSchedule.query.get_or_404(schedule_id)
    
    if schedule.status == 'completed':
        flash('Não é possível editar um agendamento de manutenção concluído.', 'warning')
        return redirect(url_for('maintenance.view_schedule', schedule_id=schedule.id))
    
    form = MaintenanceScheduleForm(obj=schedule)
    form.equipment_id.choices = [(e.id, f"{e.identification_number} - {e.model}") 
                                for e in Equipment.query.all()]
    
    # Get plans for the selected equipment
    plans = MaintenancePlan.query.filter_by(equipment_id=schedule.equipment_id).all()
    form.maintenance_plan_id.choices = [(p.id, p.name) for p in plans]
    
    if form.validate_on_submit():
        schedule.equipment_id = form.equipment_id.data
        schedule.maintenance_plan_id = form.maintenance_plan_id.data
        schedule.scheduled_date = form.scheduled_date.data
        schedule.notes = form.notes.data
        
        db.session.commit()
        
        # Update notifications
        equipment = Equipment.query.get(form.equipment_id.data)
        
        # Update all technicians notifications
        notifications = Notification.query.filter_by(schedule_id=schedule.id).all()
        for notification in notifications:
            notification.title = 'Agendamento de Manutenção Atualizado'
            notification.message = f'Manutenção para {equipment.identification_number} ({equipment.model}) foi reagendada para {form.scheduled_date.data.strftime("%Y-%m-%d %H:%M")}.'
            notification.read = False
            notification.created_at = datetime.utcnow()
        
        db.session.commit()
        flash('Agendamento de manutenção foi atualizado e os técnicos foram notificados!', 'success')
        return redirect(url_for('maintenance.schedule_list'))
    
    return render_template('maintenance/edit_schedule.html', form=form, schedule=schedule)

@maintenance_bp.route('/schedule/<int:schedule_id>/delete', methods=['POST'])
@login_required
def delete_schedule(schedule_id):
    """Delete scheduled maintenance"""
    if not current_user.is_admin():
        flash('Acesso negado. Apenas administradores podem excluir agendamentos.', 'danger')
        return redirect(url_for('maintenance.schedule_list'))
    
    schedule = MaintenanceSchedule.query.get_or_404(schedule_id)
    
    try:
        # Delete all notifications for this schedule
        Notification.query.filter_by(schedule_id=schedule.id).delete()
        
        db.session.delete(schedule)
        db.session.commit()
        flash('Agendamento de manutenção foi excluído!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir agendamento: {str(e)}', 'danger')
    
    return redirect(url_for('maintenance.schedule_list'))

# === Maintenance Records ===

@maintenance_bp.route('/records')
@login_required
def records():
    """Display all maintenance records"""
    if current_user.is_admin() or current_user.is_supervisor():
        records = MaintenanceRecord.query.order_by(MaintenanceRecord.start_time.desc()).all()
    else:
        records = MaintenanceRecord.query.filter_by(
            technician_id=current_user.id
        ).order_by(MaintenanceRecord.start_time.desc()).all()
    
    return render_template('maintenance/records.html', records=records)

@maintenance_bp.route('/schedule/<int:schedule_id>/perform', methods=['GET', 'POST'])
@login_required
def perform_maintenance(schedule_id):
    """Perform maintenance on a scheduled item"""
    schedule = MaintenanceSchedule.query.get_or_404(schedule_id)
    
    # Check if maintenance is already completed
    if schedule.status == 'completed':
        flash('Esta tarefa de manutenção já foi concluída.', 'info')
        return redirect(url_for('maintenance.view_schedule', schedule_id=schedule.id))
    
    # Get the checklist for this maintenance plan
    checklist_template = ChecklistTemplate.query.filter_by(
        maintenance_plan_id=schedule.maintenance_plan_id
    ).first()
    
    if not checklist_template:
        flash('Nenhum modelo de checklist encontrado para este plano de manutenção.', 'warning')
        return redirect(url_for('maintenance.view_schedule', schedule_id=schedule.id))
    
    # Get checklist items
    checklist_items = ChecklistItem.query.filter_by(
        template_id=checklist_template.id
    ).order_by(ChecklistItem.order).all()
    
    form = MaintenanceRecordForm()
    form.equipment_id.data = schedule.equipment_id
    form.schedule_id.data = schedule.id
    
    if request.method == 'GET':
        form.start_time.data = datetime.utcnow()
        
        # Add form entries for each checklist item
        for item in checklist_items:
            form.checklist_results.append_entry({
                'checklist_item_id': item.id,
                'status': 'pending',
                'notes': ''
            })
    
    if form.validate_on_submit():
        # Create the maintenance record
        record = MaintenanceRecord(
            equipment_id=form.equipment_id.data,
            technician_id=current_user.id,
            schedule_id=form.schedule_id.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data if form.status.data == 'completed' else None,
            status=form.status.data,
            notes=form.notes.data,
            issues_found=form.issues_found.data,
            actions_taken=form.actions_taken.data
        )
        
        db.session.add(record)
        db.session.commit()
        
        # Add the checklist results
        for item_form in form.checklist_results:
            result = ChecklistResult(
                maintenance_record_id=record.id,
                checklist_item_id=item_form.checklist_item_id.data,
                status=item_form.status.data,
                notes=item_form.notes.data
            )
            db.session.add(result)
        
        # Update the schedule status if maintenance is completed
        if form.status.data == 'completed':
            schedule.status = 'completed'
            
            # Update equipment's last maintenance date
            equipment = Equipment.query.get(schedule.equipment_id)
            equipment.last_maintenance_date = form.end_time.data
            
            # Create notification for supervisor
            supervisors = User.query.filter_by(role='supervisor').all()
            for supervisor in supervisors:
                notification = Notification(
                    user_id=supervisor.id,
                    schedule_id=schedule.id,
                    title='Manutenção Concluída',
                    message=f'Manutenção para {equipment.identification_number} ({equipment.model}) foi concluída por {current_user.first_name} {current_user.last_name}.'
                )
                db.session.add(notification)
        
        db.session.commit()
        flash('Registro de manutenção foi salvo!', 'success')
        return redirect(url_for('maintenance.records'))
    
    return render_template(
        'maintenance/checklist.html', 
        form=form, 
        schedule=schedule, 
        checklist_items=checklist_items
    )

@maintenance_bp.route('/records/<int:record_id>', methods=['GET'])
@login_required
def view_record(record_id):
    """View maintenance record details"""
    record = MaintenanceRecord.query.get_or_404(record_id)
    
    # Get checklist results
    checklist_results = ChecklistResult.query.filter_by(
        maintenance_record_id=record.id
    ).all()
    
    return render_template(
        'maintenance/view_record.html', 
        record=record, 
        checklist_results=checklist_results
    )

# === Notifications ===

@maintenance_bp.route('/notifications')
@login_required
def notifications():
    """Display all notifications for the current user"""
    user_notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    return render_template('maintenance/notifications.html', notifications=user_notifications)

@maintenance_bp.route('/notifications/<int:notification_id>/mark_read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        flash('Acesso negado. Esta notificação não pertence a você.', 'danger')
        return redirect(url_for('maintenance.notifications'))
    
    notification.read = True
    db.session.commit()
    
    return redirect(url_for('maintenance.notifications'))

@maintenance_bp.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read for the current user"""
    Notification.query.filter_by(user_id=current_user.id, read=False).update({'read': True})
    db.session.commit()
    flash('Todas as notificações foram marcadas como lidas.', 'success')
    
    return redirect(url_for('maintenance.notifications'))
