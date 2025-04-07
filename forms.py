from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
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

# Classes de validação para o arquivo
class FileSize:
    """Valida o tamanho do arquivo"""
    def __init__(self, max_size=5*1024*1024, message=None):
        self.max_size = max_size
        self.message = message

    def __call__(self, form, field):
        if field.data:
            if hasattr(field.data, 'content_length') and field.data.content_length > self.max_size:
                raise ValidationError(self.message or f'O arquivo excede o tamanho máximo de {self.max_size/1024/1024:.1f}MB')
            
            # Se não tem content_length, tenta ler o conteúdo para verificar o tamanho
            if hasattr(field.data, 'read') and not hasattr(field.data, 'content_length'):
                field.data.seek(0, 2)  # Move para o final do arquivo
                size = field.data.tell()  # Tamanho atual
                field.data.seek(0)  # Volta ao início
                if size > self.max_size:
                    raise ValidationError(self.message or f'O arquivo excede o tamanho máximo de {self.max_size/1024/1024:.1f}MB')

# Formulário para o Diário de Manutenção (Ata)
class DiarioManutencaoForm(FlaskForm):
    """
    Formulário para registrar entradas no Diário de Manutenção.
    Permite registrar atividades de manutenção com texto e opcionalmente anexar arquivos.
    """
    titulo = StringField('Título', validators=[DataRequired(), Length(min=3, max=200)])
    conteudo = TextAreaField('Conteúdo', validators=[DataRequired()])
    equipment_id = SelectField('Equipamento (Opcional)', coerce=int, validators=[Optional()])
    arquivo = FileField('Anexar Arquivo (Opcional)', validators=[
        Optional(),
        # Limitando o tamanho do arquivo para 5MB
        FileSize(max_size=5 * 1024 * 1024, message='O arquivo não pode ser maior que 5MB.'),
        # Restringindo tipos de arquivo
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 
                    'Apenas arquivos PDF, imagens, documentos Office e TXT são permitidos.')
    ])
    submit = SubmitField('Salvar')
