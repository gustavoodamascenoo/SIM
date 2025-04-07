import csv
import io
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import base64
from flask import url_for
from models import MaintenanceRecord, ChecklistResult, Equipment, User

def generate_csv(data, headers):
    """Generate a CSV file from data"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in data:
        writer.writerow(row)
    return output.getvalue()

def maintenance_history_to_csv(records):
    """Convert maintenance records to CSV format"""
    headers = ['ID', 'Equipment', 'Technician', 'Start Time', 'End Time', 'Status', 'Issues', 'Actions']
    data = []
    
    for record in records:
        equipment = Equipment.query.get(record.equipment_id)
        technician = User.query.get(record.technician_id)
        data.append([
            record.id,
            f"{equipment.identification_number} - {equipment.model}",
            f"{technician.first_name} {technician.last_name}",
            record.start_time.strftime('%Y-%m-%d %H:%M'),
            record.end_time.strftime('%Y-%m-%d %H:%M') if record.end_time else 'N/A',
            record.status,
            record.issues_found or 'None',
            record.actions_taken or 'None'
        ])
    
    return generate_csv(data, headers)

def equipment_status_to_csv(equipment_list):
    """Convert equipment status to CSV format"""
    headers = ['ID', 'Identification Number', 'Model', 'Manufacturer', 'Location', 'Status', 'Last Maintenance']
    data = []
    
    for equip in equipment_list:
        data.append([
            equip.id,
            equip.identification_number,
            equip.model,
            equip.manufacturer,
            f"{equip.location_building}, Floor {equip.location_floor}, Room {equip.location_room}",
            equip.status,
            equip.last_maintenance_date.strftime('%Y-%m-%d') if equip.last_maintenance_date else 'Never'
        ])
    
    return generate_csv(data, headers)

def technician_performance_to_csv(technicians, start_date, end_date):
    """Convert technician performance data to CSV format"""
    headers = ['Technician', 'Completed Maintenance Tasks', 'Average Duration (hours)', 'Issues Found']
    data = []
    
    for tech in technicians:
        records = MaintenanceRecord.query.filter(
            MaintenanceRecord.technician_id == tech.id,
            MaintenanceRecord.start_time >= start_date,
            MaintenanceRecord.start_time <= end_date
        ).all()
        
        completed = len([r for r in records if r.status == 'completed'])
        durations = []
        issues_count = 0
        
        for r in records:
            if r.status == 'completed' and r.end_time:
                duration = (r.end_time - r.start_time).total_seconds() / 3600  # Convert to hours
                durations.append(duration)
            if r.issues_found and r.issues_found.strip():
                issues_count += 1
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        data.append([
            f"{tech.first_name} {tech.last_name}",
            completed,
            f"{avg_duration:.2f}",
            issues_count
        ])
    
    return generate_csv(data, headers)

def get_maintenance_summary(start_date, end_date):
    """Get maintenance summary data for visualization"""
    records = MaintenanceRecord.query.filter(
        MaintenanceRecord.start_time >= start_date,
        MaintenanceRecord.start_time <= end_date
    ).all()
    
    # Group by status
    status_counts = {'completed': 0, 'in_progress': 0}
    for record in records:
        status_counts[record.status] = status_counts.get(record.status, 0) + 1
    
    # Group by date
    date_counts = {}
    for record in records:
        date_str = record.start_time.strftime('%Y-%m-%d')
        date_counts[date_str] = date_counts.get(date_str, 0) + 1
    
    # Get maintenance by equipment type
    equipment_counts = {}
    for record in records:
        equipment = Equipment.query.get(record.equipment_id)
        equip_type = f"{equipment.manufacturer} {equipment.model}"
        equipment_counts[equip_type] = equipment_counts.get(equip_type, 0) + 1
    
    return {
        'status_counts': status_counts,
        'date_counts': date_counts,
        'equipment_counts': equipment_counts
    }

def get_technician_performance(start_date, end_date):
    """Get technician performance data for visualization"""
    technicians = User.query.filter(User.role == 'technician').all()
    performance_data = []
    
    for tech in technicians:
        records = MaintenanceRecord.query.filter(
            MaintenanceRecord.technician_id == tech.id,
            MaintenanceRecord.start_time >= start_date,
            MaintenanceRecord.start_time <= end_date,
            MaintenanceRecord.status == 'completed'
        ).all()
        
        if not records:
            continue
            
        completed_count = len(records)
        
        # Calculate average completion time
        durations = []
        for r in records:
            if r.end_time:
                duration = (r.end_time - r.start_time).total_seconds() / 3600  # Convert to hours
                durations.append(duration)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        performance_data.append({
            'name': f"{tech.first_name} {tech.last_name}",
            'completed': completed_count,
            'avg_duration': avg_duration
        })
    
    return performance_data

def get_equipment_status_summary():
    """Get equipment status summary for visualization"""
    equipment_list = Equipment.query.all()
    status_counts = {'active': 0, 'inactive': 0, 'maintenance': 0}
    
    for equip in equipment_list:
        status_counts[equip.status] = status_counts.get(equip.status, 0) + 1
    
    # Get equipment by manufacturer
    manufacturer_counts = {}
    for equip in equipment_list:
        manufacturer_counts[equip.manufacturer] = manufacturer_counts.get(equip.manufacturer, 0) + 1
    
    return {
        'status_counts': status_counts,
        'manufacturer_counts': manufacturer_counts
    }

def generate_status_chart(status_data):
    """Generate a pie chart of equipment status"""
    plt.figure(figsize=(8, 6))
    
    # Tradução dos status
    status_labels = {
        'active': 'Ativo',
        'inactive': 'Inativo',
        'maintenance': 'Em Manutenção'
    }
    
    # Obter labels traduzidos
    labels = [status_labels.get(key, key) for key in status_data.keys()]
    sizes = list(status_data.values())
    colors = ['#3498db', '#e74c3c', '#f39c12']
    
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('Distribuição de Status dos Equipamentos')
    
    # Convert plot to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    # Encode the bytes to base64 string
    encoded = base64.b64encode(image_png).decode('utf-8')
    return f"data:image/png;base64,{encoded}"

def generate_maintenance_timeline(date_data):
    """Generate a timeline chart of maintenance activities"""
    plt.figure(figsize=(12, 6))
    
    # Sort dates
    sorted_dates = sorted(date_data.keys())
    counts = [date_data[date] for date in sorted_dates]
    
    plt.bar(sorted_dates, counts, color='#2ecc71')
    plt.xticks(rotation=45)
    plt.xlabel('Data')
    plt.ylabel('Número de Atividades de Manutenção')
    plt.title('Linha do Tempo de Atividades de Manutenção')
    plt.tight_layout()
    
    # Convert plot to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    # Encode the bytes to base64 string
    encoded = base64.b64encode(image_png).decode('utf-8')
    return f"data:image/png;base64,{encoded}"

def generate_technician_chart(performance_data):
    """Generate a bar chart of technician performance"""
    plt.figure(figsize=(10, 6))
    
    names = [tech['name'] for tech in performance_data]
    completed = [tech['completed'] for tech in performance_data]
    avg_durations = [tech['avg_duration'] for tech in performance_data]
    
    x = range(len(names))
    width = 0.35
    
    plt.bar([i - width/2 for i in x], completed, width, label='Tarefas Concluídas', color='#3498db')
    plt.bar([i + width/2 for i in x], avg_durations, width, label='Duração Média (horas)', color='#e74c3c')
    
    plt.xlabel('Técnicos')
    plt.ylabel('Contagem / Horas')
    plt.title('Desempenho dos Técnicos')
    plt.xticks(x, names, rotation=45)
    plt.legend()
    plt.tight_layout()
    
    # Convert plot to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    # Encode the bytes to base64 string
    encoded = base64.b64encode(image_png).decode('utf-8')
    return f"data:image/png;base64,{encoded}"

def generate_equipment_manufacturer_chart(manufacturer_data):
    """Generate a bar chart of equipment by manufacturer"""
    plt.figure(figsize=(10, 6))
    
    manufacturers = list(manufacturer_data.keys())
    counts = list(manufacturer_data.values())
    
    plt.bar(manufacturers, counts, color='#9b59b6')
    plt.xlabel('Fabricante')
    plt.ylabel('Número de Equipamentos')
    plt.title('Distribuição de Equipamentos por Fabricante')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Convert plot to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    # Encode the bytes to base64 string
    encoded = base64.b64encode(image_png).decode('utf-8')
    return f"data:image/png;base64,{encoded}"
