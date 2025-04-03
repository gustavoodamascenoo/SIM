from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, FloatField, TextAreaField, SelectField
from wtforms import BooleanField, IntegerField, DateTimeField, HiddenField, FieldList, FormField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from models import User

class LoginForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar Acesso')
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Nome', validators=[DataRequired()])
    last_name = StringField('Sobrenome', validators=[DataRequired()])
    phone = StringField('Telefone', validators=[Optional()])
    role = SelectField('Função', choices=[
        ('technician', 'Técnico'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Administrador')
    ], validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Cadastrar')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Nome de usuário já existe. Por favor, escolha outro.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email já registrado. Por favor, use outro endereço de email.')

class EquipmentForm(FlaskForm):
    identification_number = StringField('Número de Identificação', validators=[DataRequired()])
    model = StringField('Modelo', validators=[DataRequired()])
    manufacturer = StringField('Fabricante', validators=[DataRequired()])
    power = FloatField('Potência (kW)', validators=[DataRequired(), NumberRange(min=0)])
    installation_date = DateField('Data de Instalação', validators=[DataRequired()])
    location_building = StringField('Prédio', validators=[DataRequired()])
    location_floor = IntegerField('Andar', validators=[DataRequired()])
    location_room = StringField('Sala', validators=[DataRequired()])
    location_details = StringField('Detalhes de Localização', validators=[Optional()])
    serial_number = StringField('Número de Série', validators=[Optional()])
    warranty_end_date = DateField('Data de Término da Garantia', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('maintenance', 'Em Manutenção')
    ], validators=[DataRequired()])
    notes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Enviar')

class MaintenancePlanForm(FlaskForm):
    equipment_id = SelectField('Equipamento', coerce=int, validators=[DataRequired()])
    name = StringField('Nome do Plano', validators=[DataRequired()])
    description = TextAreaField('Descrição', validators=[Optional()])
    frequency_days = IntegerField('Frequência (dias)', validators=[DataRequired(), NumberRange(min=1)])
    is_active = BooleanField('Ativo')
    submit = SubmitField('Enviar')

class ChecklistItemForm(FlaskForm):
    description = StringField('Descrição da Tarefa', validators=[DataRequired()])
    is_required = BooleanField('Obrigatório', default=True)
    order = HiddenField('Ordem')

class ChecklistTemplateForm(FlaskForm):
    maintenance_plan_id = SelectField('Plano de Manutenção', coerce=int, validators=[DataRequired()])
    name = StringField('Nome do Modelo', validators=[DataRequired()])
    description = TextAreaField('Descrição', validators=[Optional()])
    items = FieldList(FormField(ChecklistItemForm), min_entries=1)
    add_item = SubmitField('Adicionar Item')
    submit = SubmitField('Enviar')

class MaintenanceScheduleForm(FlaskForm):
    equipment_id = SelectField('Equipamento', coerce=int, validators=[DataRequired()])
    maintenance_plan_id = SelectField('Plano de Manutenção', coerce=int, validators=[DataRequired()])
    scheduled_date = DateTimeField('Data Agendada', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    notes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Agendar Manutenção')

class ChecklistResultForm(FlaskForm):
    checklist_item_id = HiddenField('ID do Item de Checklist')
    status = SelectField('Status', choices=[
        ('completed', 'Concluído'),
        ('pending', 'Pendente'),
        ('not_applicable', 'Não Aplicável')
    ], validators=[DataRequired()])
    notes = TextAreaField('Observações', validators=[Optional()])

class MaintenanceRecordForm(FlaskForm):
    equipment_id = HiddenField('ID do Equipamento')
    schedule_id = HiddenField('ID do Agendamento')
    start_time = DateTimeField('Hora de Início', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    end_time = DateTimeField('Hora de Término', format='%Y-%m-%d %H:%M', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluído')
    ], validators=[DataRequired()])
    notes = TextAreaField('Observações', validators=[Optional()])
    issues_found = TextAreaField('Problemas Encontrados', validators=[Optional()])
    actions_taken = TextAreaField('Ações Tomadas', validators=[Optional()])
    checklist_results = FieldList(FormField(ChecklistResultForm))
    submit = SubmitField('Enviar')

class ReportForm(FlaskForm):
    start_date = DateField('Data Inicial', validators=[DataRequired()])
    end_date = DateField('Data Final', validators=[DataRequired()])
    equipment_id = SelectField('Equipamento', coerce=int, validators=[Optional()])
    technician_id = SelectField('Técnico', coerce=int, validators=[Optional()])
    status = SelectField('Status', choices=[
        ('all', 'Todos'),
        ('completed', 'Concluído'),
        ('pending', 'Pendente'),
        ('in_progress', 'Em Andamento')
    ], validators=[Optional()])
    submit = SubmitField('Gerar Relatório')

class ExportForm(FlaskForm):
    report_type = SelectField('Tipo de Relatório', choices=[
        ('maintenance_history', 'Histórico de Manutenção'),
        ('equipment_status', 'Status dos Equipamentos'),
        ('technician_performance', 'Desempenho dos Técnicos')
    ], validators=[DataRequired()])
    start_date = DateField('Data Inicial', validators=[DataRequired()])
    end_date = DateField('Data Final', validators=[DataRequired()])
    submit = SubmitField('Exportar para CSV')
