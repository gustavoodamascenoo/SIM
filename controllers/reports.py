from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from models import Equipment, MaintenancePlan, MaintenanceRecord, User
from forms import ReportForm, ExportForm
from utils import (
    maintenance_history_to_csv, equipment_status_to_csv, technician_performance_to_csv,
    get_maintenance_summary, get_technician_performance, get_equipment_status_summary,
    generate_status_chart, generate_maintenance_timeline, generate_technician_chart,
    generate_equipment_manufacturer_chart
)

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    """Display report options"""
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Access denied. Reports are available only to administrators and supervisors.', 'danger')
        return redirect(url_for('maintenance.dashboard'))
    
    return render_template('reports/index.html')

@reports_bp.route('/maintenance_history', methods=['GET', 'POST'])
@login_required
def maintenance_history():
    """Display maintenance history report"""
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Access denied. Reports are available only to administrators and supervisors.', 'danger')
        return redirect(url_for('maintenance.dashboard'))
    
    form = ReportForm()
    
    # Default to last 30 days if no dates provided
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Populate equipment choices
    equipment_choices = [(0, 'All Equipment')]
    equipment_choices.extend([(e.id, f"{e.identification_number} - {e.model}") 
                           for e in Equipment.query.all()])
    form.equipment_id.choices = equipment_choices
    
    # Populate technician choices
    technician_choices = [(0, 'All Technicians')]
    technician_choices.extend([(t.id, f"{t.first_name} {t.last_name}") 
                            for t in User.query.filter_by(role='technician').all()])
    form.technician_id.choices = technician_choices
    
    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
        equipment_id = form.equipment_id.data
        technician_id = form.technician_id.data
        status = form.status.data
        
        # Query maintenance records based on filter criteria
        query = MaintenanceRecord.query.filter(
            MaintenanceRecord.start_time >= start_date,
            MaintenanceRecord.start_time <= end_date
        )
        
        if equipment_id != 0:
            query = query.filter(MaintenanceRecord.equipment_id == equipment_id)
        
        if technician_id != 0:
            query = query.filter(MaintenanceRecord.technician_id == technician_id)
        
        if status != 'all':
            query = query.filter(MaintenanceRecord.status == status)
        
        records = query.order_by(MaintenanceRecord.start_time.desc()).all()
    else:
        # Default query for GET requests
        records = MaintenanceRecord.query.filter(
            MaintenanceRecord.start_time >= start_date,
            MaintenanceRecord.start_time <= end_date
        ).order_by(MaintenanceRecord.start_time.desc()).all()
    
    return render_template(
        'reports/maintenance_history.html',
        form=form,
        records=records,
        start_date=start_date,
        end_date=end_date
    )

@reports_bp.route('/equipment_status')
@login_required
def equipment_status():
    """Display equipment status report"""
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Access denied. Reports are available only to administrators and supervisors.', 'danger')
        return redirect(url_for('maintenance.dashboard'))
    
    equipment_list = Equipment.query.all()
    
    # Group by status
    status_counts = {'active': 0, 'inactive': 0, 'maintenance': 0}
    for equip in equipment_list:
        status_counts[equip.status] = status_counts.get(equip.status, 0) + 1
    
    # Group by manufacturer
    manufacturer_counts = {}
    for equip in equipment_list:
        manufacturer_counts[equip.manufacturer] = manufacturer_counts.get(equip.manufacturer, 0) + 1
    
    # Equipment needing maintenance soon (no maintenance in 30+ days)
    today = datetime.utcnow()
    thirty_days_ago = today - timedelta(days=30)
    
    needs_maintenance = []
    for equip in equipment_list:
        if equip.status != 'inactive':
            if not equip.last_maintenance_date or equip.last_maintenance_date < thirty_days_ago:
                needs_maintenance.append(equip)
    
    return render_template(
        'reports/equipment_status.html',
        equipment_list=equipment_list,
        status_counts=status_counts,
        manufacturer_counts=manufacturer_counts,
        needs_maintenance=needs_maintenance
    )

@reports_bp.route('/technician_performance', methods=['GET', 'POST'])
@login_required
def technician_performance():
    """Display technician performance report"""
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Access denied. Reports are available only to administrators and supervisors.', 'danger')
        return redirect(url_for('maintenance.dashboard'))
    
    form = ReportForm()
    
    # Default to last 30 days if no dates provided
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Only need date fields for this form
    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
    
    # Get all technicians
    technicians = User.query.filter_by(role='technician').all()
    
    # Get performance data for each technician
    technician_data = []
    for tech in technicians:
        records = MaintenanceRecord.query.filter(
            MaintenanceRecord.technician_id == tech.id,
            MaintenanceRecord.start_time >= start_date,
            MaintenanceRecord.start_time <= end_date
        ).all()
        
        completed = len([r for r in records if r.status == 'completed'])
        in_progress = len([r for r in records if r.status == 'in_progress'])
        total = len(records)
        
        # Calculate average maintenance duration for completed tasks
        durations = []
        for r in records:
            if r.status == 'completed' and r.end_time:
                duration = (r.end_time - r.start_time).total_seconds() / 3600  # Convert to hours
                durations.append(duration)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        technician_data.append({
            'technician': tech,
            'completed': completed,
            'in_progress': in_progress,
            'total': total,
            'avg_duration': avg_duration
        })
    
    return render_template(
        'reports/technician_performance.html',
        form=form,
        technician_data=technician_data,
        start_date=start_date,
        end_date=end_date
    )

@reports_bp.route('/data_visualization', methods=['GET'])
@login_required
def data_visualization():
    """Display BI-style data visualization"""
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Access denied. Reports are available only to administrators and supervisors.', 'danger')
        return redirect(url_for('maintenance.dashboard'))
    
    # Get date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=90)  # Last 90 days
    
    # Get maintenance summary data
    maintenance_summary = get_maintenance_summary(start_date, end_date)
    
    # Get equipment status data
    equipment_status = get_equipment_status_summary()
    
    # Get technician performance data
    technician_performance = get_technician_performance(start_date, end_date)
    
    # Generate chart images
    status_chart = generate_status_chart(equipment_status['status_counts'])
    timeline_chart = generate_maintenance_timeline(maintenance_summary['date_counts'])
    technician_chart = generate_technician_chart(technician_performance)
    manufacturer_chart = generate_equipment_manufacturer_chart(equipment_status['manufacturer_counts'])
    
    # Get equipment needing maintenance soon
    today = datetime.utcnow()
    thirty_days_ago = today - timedelta(days=30)
    
    equipment_list = Equipment.query.all()
    needs_maintenance = []
    for equip in equipment_list:
        if equip.status != 'inactive':
            if not equip.last_maintenance_date or equip.last_maintenance_date < thirty_days_ago:
                needs_maintenance.append(equip)
    
    return render_template(
        'reports/data_visualization.html',
        status_chart=status_chart,
        timeline_chart=timeline_chart,
        technician_chart=technician_chart,
        manufacturer_chart=manufacturer_chart,
        start_date=start_date,
        end_date=end_date,
        status_counts=equipment_status['status_counts'],
        manufacturer_counts=equipment_status['manufacturer_counts'],
        needs_maintenance=needs_maintenance
    )

@reports_bp.route('/export', methods=['GET', 'POST'])
@login_required
def export():
    """Export reports to CSV"""
    if not (current_user.is_admin() or current_user.is_supervisor()):
        flash('Access denied. Reports are available only to administrators and supervisors.', 'danger')
        return redirect(url_for('maintenance.dashboard'))
    
    form = ExportForm()
    
    if form.validate_on_submit():
        report_type = form.report_type.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        
        if report_type == 'maintenance_history':
            # Query maintenance records
            records = MaintenanceRecord.query.filter(
                MaintenanceRecord.start_time >= start_date,
                MaintenanceRecord.start_time <= end_date
            ).order_by(MaintenanceRecord.start_time.desc()).all()
            
            # Generate CSV
            csv_data = maintenance_history_to_csv(records)
            filename = f"maintenance_history_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
            
            return Response(
                csv_data,
                mimetype="text/csv",
                headers={"Content-disposition": f"attachment; filename={filename}"}
            )
        
        elif report_type == 'equipment_status':
            # Get all equipment
            equipment_list = Equipment.query.all()
            
            # Generate CSV
            csv_data = equipment_status_to_csv(equipment_list)
            filename = f"equipment_status_{datetime.utcnow().strftime('%Y%m%d')}.csv"
            
            return Response(
                csv_data,
                mimetype="text/csv",
                headers={"Content-disposition": f"attachment; filename={filename}"}
            )
        
        elif report_type == 'technician_performance':
            # Get all technicians
            technicians = User.query.filter_by(role='technician').all()
            
            # Generate CSV
            csv_data = technician_performance_to_csv(technicians, start_date, end_date)
            filename = f"technician_performance_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
            
            return Response(
                csv_data,
                mimetype="text/csv",
                headers={"Content-disposition": f"attachment; filename={filename}"}
            )
    
    return render_template('reports/export.html', form=form)
