from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()

# Garantir que datetime está disponível globalmente
datetime = datetime
from app import db, app  
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
    """Exclui um plano de manutenção"""
    if not current_user.is_admin():
        flash('Acesso negado. Apenas administradores podem excluir planos.', 'danger')
        return redirect(url_for('maintenance.plans'))
    
    plan = MaintenancePlan.query.get_or_404(plan_id)
    
    try:
        db.session.delete(plan)
        db.session.commit()
        flash(f'Plano "{plan.name}" excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'danger')
    
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
        if 'maintenance_plan_id' in request.form and 'name' in request.form:
            try:
                maintenance_plan_id = int(request.form['maintenance_plan_id'])
                name = request.form['name']
                description = request.form.get('description', '')
                
                # Create the checklist template
                checklist = ChecklistTemplate(
                    maintenance_plan_id=maintenance_plan_id,
                    name=name,
                    description=description
                )
                db.session.add(checklist)
                db.session.commit()
                
                # Get items from form
                item_descriptions = request.form.getlist('item_descriptions[]')
                item_required = request.form.getlist('item_required[]')
                
                # Process items
                for i, description in enumerate(item_descriptions):
                    if description:  # Only add non-empty descriptions
                        is_required = i < len(item_required) and item_required[i] == 'true'
                        print(f"Processing item {i}: {description}, Required: {is_required}")
                        
                        item = ChecklistItem(
                            template_id=checklist.id,
                            description=description,
                            is_required=is_required,
                            order=i+1
                        )
                        db.session.add(item)
                
                db.session.commit()
                flash(f'Modelo de checklist "{name}" foi criado com sucesso!', 'success')
                return redirect(url_for('maintenance.checklists'))
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao criar checklist: {str(e)}', 'danger')
                print(f"Error creating checklist: {str(e)}")
        else:
            flash('Dados de formulário incompletos. Por favor, preencha todos os campos obrigatórios.', 'danger')
    
    return render_template('maintenance/add_checklist.html', form=form)

@maintenance_bp.route('/checklists/<int:checklist_id>/view', methods=['GET'])
@login_required
def view_checklist(checklist_id):
    """View checklist template details"""
    template = ChecklistTemplate.query.get_or_404(checklist_id)
    return render_template('maintenance/view_checklist.html', template=template)

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
    
    # Get all existing checklist items
    checklist_items = ChecklistItem.query.filter_by(template_id=checklist.id).order_by(ChecklistItem.order).all()
    
    if request.method == 'POST':
        if 'maintenance_plan_id' in request.form and 'name' in request.form:
            try:
                maintenance_plan_id = int(request.form['maintenance_plan_id'])
                name = request.form['name']
                description = request.form.get('description', '')
                
                # Update checklist template
                checklist.maintenance_plan_id = maintenance_plan_id
                checklist.name = name
                checklist.description = description
                
                # Delete existing items
                ChecklistItem.query.filter_by(template_id=checklist.id).delete()
                
                # Get items from form
                item_descriptions = request.form.getlist('item_descriptions[]')
                item_required = request.form.getlist('item_required[]')
                
                # Process items
                for i, description in enumerate(item_descriptions):
                    if description:  # Only add non-empty descriptions
                        is_required = i < len(item_required) and item_required[i] == 'true'
                        print(f"Processing item {i}: {description}, Required: {is_required}")
                        
                        item = ChecklistItem(
                            template_id=checklist.id,
                            description=description,
                            is_required=is_required,
                            order=i+1
                        )
                        db.session.add(item)
                
                db.session.commit()
                flash(f'Modelo de checklist "{name}" foi atualizado com sucesso!', 'success')
                return redirect(url_for('maintenance.checklists'))
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao atualizar checklist: {str(e)}', 'danger')
                print(f"Error updating checklist: {str(e)}")
        else:
            flash('Dados de formulário incompletos. Por favor, preencha todos os campos obrigatórios.', 'danger')
    
    return render_template('maintenance/edit_checklist.html', form=form, checklist=checklist, checklist_items=checklist_items)

@maintenance_bp.route('/checklists/<int:checklist_id>/delete', methods=['POST'])
@login_required
def delete_checklist(checklist_id):
    """Exclui um modelo de checklist"""
    if not current_user.is_admin():
        flash('Acesso negado. Apenas administradores podem excluir checklists.', 'danger')
        return redirect(url_for('maintenance.checklists'))
    
    checklist = ChecklistTemplate.query.get_or_404(checklist_id)
    
    try:
        # Primeiro exclui os itens associados
        ChecklistItem.query.filter_by(template_id=checklist.id).delete()
        # Depois exclui o checklist
        db.session.delete(checklist)
        db.session.commit()
        flash(f'Checklist "{checklist.name}" excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'danger')
    
    return redirect(url_for('maintenance.checklists'))

# === Scheduling ===
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


@maintenance_bp.route('/get_plans/<int:equipment_id>')
@login_required

@csrf.exempt  # Desativa o CSRF para esta rota específica
def get_plans(equipment_id):
    """Rota para obter planos de manutenção por equipamento (AJAX)"""
    plans = MaintenancePlan.query.filter_by(equipment_id=equipment_id).all()
    return jsonify([(p.id, p.name) for p in plans])
@maintenance_bp.route('/schedule/add', methods=['GET', 'POST'])
@login_required
def add_schedule():
    """Add a new maintenance schedule"""
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Acesso negado. Você não tem permissão para agendar manutenções.', 'danger')
        return redirect(url_for('maintenance.schedule_list'))
    
    form = MaintenanceScheduleForm()
    form.equipment_id.choices = [(e.id, f"{e.identification_number} - {e.model}") 
                               for e in Equipment.query.all()]
    
    # Carrega os planos se já houver um equipamento selecionado (caso de falha na validação)
    if request.method == 'POST' and form.equipment_id.data:
        plans = MaintenancePlan.query.filter_by(equipment_id=form.equipment_id.data).all()
        form.maintenance_plan_id.choices = [(p.id, p.name) for p in plans]
    else:
        form.maintenance_plan_id.choices = []

    if form.validate_on_submit():
        try:
            schedule = MaintenanceSchedule(
                equipment_id=form.equipment_id.data,
                maintenance_plan_id=form.maintenance_plan_id.data,
                scheduled_date=form.scheduled_date.data,
                notes=form.notes.data,
                status='scheduled'
            )
            
            db.session.add(schedule)
            db.session.commit()
            
            # Notificar técnicos
            equipment = Equipment.query.get(form.equipment_id.data)
            technicians = User.query.filter_by(role='technician').all()
            
            for tech in technicians:
                notification = Notification(
                    user_id=tech.id,
                    schedule_id=schedule.id,
                    title='Nova Manutenção Agendada',
                    message=f'Manutenção para {equipment.identification_number} ({equipment.model}) '
                           f'agendada para {form.scheduled_date.data.strftime("%d/%m/%Y %H:%M")}'
                )
                db.session.add(notification)
            
            db.session.commit()
            flash('Manutenção agendada com sucesso!', 'success')
            return redirect(url_for('maintenance.schedule_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao agendar manutenção: {str(e)}', 'danger')
    
    # Se houver erros de validação, mantém os dados selecionados
    elif request.method == 'POST':
        flash('Por favor, corrija os erros no formulário.', 'danger')
    
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
    """Exclui um agendamento de manutenção"""
    if not current_user.is_admin():
        flash('Acesso negado. Apenas administradores podem excluir agendamentos.', 'danger')
        return redirect(url_for('maintenance.schedule_list'))
    
    schedule = MaintenanceSchedule.query.get_or_404(schedule_id)
    
    try:
        # Primeiro exclui as notificações relacionadas
        Notification.query.filter_by(schedule_id=schedule.id).delete()
        # Depois exclui o agendamento
        db.session.delete(schedule)
        db.session.commit()
        flash('Agendamento excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'danger')
    
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
    """Executar manutenção em um item agendado"""
    schedule = MaintenanceSchedule.query.get_or_404(schedule_id)

    if schedule.status == 'completed':
        flash('Esta manutenção já foi concluída', 'info')
        return redirect(url_for('maintenance.view_schedule', schedule_id=schedule.id))

    # Obtém o modelo de checklist associado ao plano de manutenção
    checklist_template = ChecklistTemplate.query.filter_by(maintenance_plan_id=schedule.maintenance_plan_id).first()

    if not checklist_template:
        flash('Nenhum checklist disponível para este plano', 'warning')
        return redirect(url_for('maintenance.view_schedule', schedule_id=schedule.id))

    # Obtém os itens do checklist associados ao modelo
    checklist_items = ChecklistItem.query.filter_by(template_id=checklist_template.id).order_by(ChecklistItem.order).all()

    form = MaintenanceRecordForm()
    form.equipment_id.data = schedule.equipment_id
    form.schedule_id.data = schedule.id

    if request.method == 'GET':
        form.start_time.data = datetime.now()
        form.status.data = 'in_progress'

        # Limpa e adiciona itens do checklist ao formulário
        form.checklist_results.entries = []
        for item in checklist_items:
            form.checklist_results.append_entry({
                'checklist_item_id': item.id,
                'status': 'pendente',
                'notes': ''
            })

    if form.validate_on_submit():
        try:
            # Cria o registro de manutenção principal
            record = MaintenanceRecord(
                equipment_id=schedule.equipment_id,
                schedule_id=schedule.id,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                status=form.status.data,
                issues_found=form.issues_found.data,
                actions_taken=form.actions_taken.data,
                notes=form.notes.data,
                technician_id=current_user.id
            )
            db.session.add(record)
            db.session.flush()  # Salva temporariamente para gerar o ID do registro

            # Processa os resultados do checklist
            for item_form in form.checklist_results.entries:
                result = ChecklistResult(
                    maintenance_record_id=record.id,
                    checklist_item_id=item_form.checklist_item_id.data,
                    status=item_form.status.data,
                    notes=item_form.notes.data
                )

                # Processa arquivo anexado, se existir
                if item_form.arquivo.data:
                    file = item_form.arquivo.data
                    result.arquivo_nome = file.filename
                    result.arquivo_dados = file.read()
                    result.arquivo_tipo = file.content_type

                db.session.add(result)

            # Atualiza o status do agendamento, se concluído
            if form.status.data == 'completed':
                schedule.status = 'completed'
                schedule.equipment.last_maintenance_date = datetime.now()

            db.session.commit()
            flash('Registro de manutenção salvo com sucesso!', 'success')
            return redirect(url_for('maintenance.records'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar registro: {str(e)}', 'danger')
            app.logger.error(f'Error saving maintenance record: {str(e)}')

    return render_template('maintenance/checklist.html',
                           form=form,
                           schedule=schedule,
                           checklist_items=checklist_items)
# === view_records ===
@maintenance_bp.route('/records/<int:record_id>', methods=['GET'])
@login_required
def view_record(record_id):
    """Visualizar detalhes de um registro de manutenção"""
    record = MaintenanceRecord.query.get_or_404(record_id)
    # Obter os resultados do checklist associados ao registro
    checklist_results = ChecklistResult.query.filter_by(maintenance_record_id=record.id).all()
    return render_template('maintenance/view_record.html',
                           record=record,
                           checklist_results=checklist_results)

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

# === Download de Arquivos ===

@maintenance_bp.route('/checklist_result/<int:result_id>/download', methods=['GET'])
@login_required
def download_checklist_file(result_id):
    """Download arquivo anexado a um item de checklist"""
    result = ChecklistResult.query.get_or_404(result_id)
    
    # Verificar se o arquivo existe
    if not result.arquivo_dados or not result.arquivo_nome or not result.arquivo_tipo:
        flash('Nenhum arquivo encontrado para este item.', 'warning')
        return redirect(url_for('maintenance.view_record', record_id=result.maintenance_record_id))
    
    # Verificar se o usuário tem permissão para acessar este registro
    record = MaintenanceRecord.query.get(result.maintenance_record_id)
    if not (current_user.is_admin() or current_user.is_supervisor() or record.technician_id == current_user.id):
        flash('Você não tem permissão para acessar este arquivo.', 'danger')
        return redirect(url_for('maintenance.records'))
    
    # Preparar o download
    from io import BytesIO
    from flask import send_file
    
    return send_file(
        BytesIO(result.arquivo_dados),
        download_name=result.arquivo_nome,
        mimetype=result.arquivo_tipo
    )
