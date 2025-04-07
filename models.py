from datetime import datetime
from enum import Enum
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class UserRole(Enum):
    ADMIN = 'admin'
    TECHNICIAN = 'technician'
    SUPERVISOR = 'supervisor'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.TECHNICIAN.value)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    
    # Relationships
    maintenance_records = db.relationship('MaintenanceRecord', backref='technician', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == UserRole.ADMIN.value
    
    def is_technician(self):
        return self.role == UserRole.TECHNICIAN.value
    
    def is_supervisor(self):
        return self.role == UserRole.SUPERVISOR.value
    
    def __repr__(self):
        return f'<User {self.username}>'

class Equipment(db.Model):
    __tablename__ = 'equipment'
    
    id = db.Column(db.Integer, primary_key=True)
    identification_number = db.Column(db.String(50), unique=True, nullable=False)
    model = db.Column(db.String(100), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)
    power = db.Column(db.Float, nullable=False)  # in kW
    installation_date = db.Column(db.Date, nullable=False)
    location_building = db.Column(db.String(100), nullable=False)
    location_floor = db.Column(db.Integer, nullable=False)
    location_room = db.Column(db.String(100), nullable=False)
    location_details = db.Column(db.String(200))
    serial_number = db.Column(db.String(100))
    warranty_end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, inactive, maintenance
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_maintenance_date = db.Column(db.DateTime)
    
    # Relationships
    maintenance_plans = db.relationship('MaintenancePlan', backref='equipment', lazy=True)
    maintenance_schedules = db.relationship('MaintenanceSchedule', backref='equipment', lazy=True)
    maintenance_records = db.relationship('MaintenanceRecord', backref='equipment', lazy=True)
    
    def __repr__(self):
        return f'<Equipment {self.identification_number}>'

class MaintenancePlan(db.Model):
    __tablename__ = 'maintenance_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    frequency_days = db.Column(db.Integer, nullable=False)  # Interval in days
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    checklist_templates = db.relationship('ChecklistTemplate', backref='maintenance_plan', lazy=True)
    
    def __repr__(self):
        return f'<MaintenancePlan {self.name} for Equipment {self.equipment_id}>'

class ChecklistTemplate(db.Model):
    __tablename__ = 'checklist_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    maintenance_plan_id = db.Column(db.Integer, db.ForeignKey('maintenance_plans.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    checklist_items = db.relationship('ChecklistItem', backref='template', lazy=True)
    
    def __repr__(self):
        return f'<ChecklistTemplate {self.name}>'

class ChecklistItem(db.Model):
    __tablename__ = 'checklist_items'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('checklist_templates.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    is_required = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<ChecklistItem {self.description}>'

class MaintenanceSchedule(db.Model):
    __tablename__ = 'maintenance_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    maintenance_plan_id = db.Column(db.Integer, db.ForeignKey('maintenance_plans.id'), nullable=False)
    scheduled_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed, canceled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Additional foreign key
    maintenance_plan = db.relationship('MaintenancePlan')
    
    # Relationships
    maintenance_record = db.relationship('MaintenanceRecord', backref='schedule', lazy=True, uselist=False)
    notifications = db.relationship('Notification', backref='schedule', lazy=True)
    
    def __repr__(self):
        return f'<MaintenanceSchedule {self.id} for Equipment {self.equipment_id}>'

class MaintenanceRecord(db.Model):
    __tablename__ = 'maintenance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('maintenance_schedules.id'))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed
    notes = db.Column(db.Text)
    issues_found = db.Column(db.Text)
    actions_taken = db.Column(db.Text)
    
    # Relationships
    checklist_results = db.relationship('ChecklistResult', backref='maintenance_record', lazy=True)
    
    def __repr__(self):
        return f'<MaintenanceRecord {self.id} by Technician {self.technician_id}>'

class ChecklistResult(db.Model):
    __tablename__ = 'checklist_results'
    
    id = db.Column(db.Integer, primary_key=True)
    maintenance_record_id = db.Column(db.Integer, db.ForeignKey('maintenance_records.id'), nullable=False)
    checklist_item_id = db.Column(db.Integer, db.ForeignKey('checklist_items.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # ok, nao_conforme, nao_se_aplica
    notes = db.Column(db.Text)
    arquivo_nome = db.Column(db.String(255), nullable=True)  # Nome do arquivo anexado
    arquivo_dados = db.Column(db.LargeBinary, nullable=True)  # Dados do arquivo binário
    arquivo_tipo = db.Column(db.String(100), nullable=True)   # Tipo MIME do arquivo
    
    # Relationship to checklist item
    checklist_item = db.relationship('ChecklistItem')
    
    def __repr__(self):
        return f'<ChecklistResult {self.id} for Item {self.checklist_item_id}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('maintenance_schedules.id'))
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'

# Modelo para o Diário de Manutenção (Ata)
class DiarioManutencao(db.Model):
    __tablename__ = 'diarios_manutencao'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=True)  # Opcional
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    arquivo_nome = db.Column(db.String(255), nullable=True)  # Nome do arquivo anexado
    arquivo_dados = db.Column(db.LargeBinary, nullable=True)  # Dados do arquivo binário
    arquivo_tipo = db.Column(db.String(100), nullable=True)   # Tipo MIME do arquivo
    
    # Relacionamentos
    usuario = db.relationship('User', backref='diarios_manutencao', lazy=True)
    equipamento = db.relationship('Equipment', backref='diarios_manutencao', lazy=True)
    
    def __repr__(self):
        return f'<DiarioManutencao {self.id}: {self.titulo}>'
