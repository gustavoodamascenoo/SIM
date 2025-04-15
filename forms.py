from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField, DateField,
                     FloatField, TextAreaField, SelectField, BooleanField,
                     IntegerField, DateTimeField, HiddenField, FieldList, FormField)
from wtforms.validators import (DataRequired, Email, EqualTo, Length,
                                ValidationError, Optional, NumberRange)
from models import User
from datetime import datetime

class FileSize:
    """Valida o tamanho do arquivo (max 5MB por padrão)"""
    def __init__(self, max_size=5 * 1024 * 1024, message=None):
        self.max_size = max_size
        self.message = message or f'O arquivo não pode exceder {self.max_size / 1024 / 1024:.1f}MB'

    def __call__(self, form, field):
        if field.data:
            file = field.data
            if hasattr(file, 'content_length'):
                size = file.content_length
            else:
                pos = file.tell()
                file.seek(0, 2)
                size = file.tell()
                file.seek(pos)
            if size > self.max_size:
                raise ValidationError(self.message)

class LoginForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar Acesso')
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário',
                           validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    first_name = StringField('Nome',
                             validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Sobrenome',
                            validators=[DataRequired(), Length(max=50)])
    phone = StringField('Telefone',
                        validators=[Optional(), Length(max=20)])
    role = SelectField('Função',
                       choices=[
                           ('technician', 'Técnico'),
                           ('supervisor', 'Supervisor'),
                           ('admin', 'Administrador')
                       ],
                       validators=[DataRequired()])
    password = PasswordField('Senha',
                             validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Cadastrar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Nome de usuário já existe. Por favor, escolha outro.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email já registrado. Por favor, use outro email.')

class EquipmentForm(FlaskForm):
    identification_number = StringField('Número de Identificação',
                                        validators=[DataRequired(), Length(max=50)])
    model = StringField('Modelo',
                        validators=[DataRequired(), Length(max=100)])
    manufacturer = StringField('Fabricante',
                               validators=[DataRequired(), Length(max=100)])
    power = FloatField('Potência (kW)',
                       validators=[DataRequired(), NumberRange(min=0)])
    installation_date = DateField('Data de Instalação',
                                  validators=[DataRequired()])
    location_building = StringField('Prédio',
                                    validators=[DataRequired(), Length(max=50)])
    location_floor = IntegerField('Andar',
                                  validators=[DataRequired(), NumberRange(min=0)])
    location_room = StringField('Sala',
                                validators=[DataRequired(), Length(max=20)])
    location_details = StringField('Detalhes de Localização',
                                   validators=[Optional(), Length(max=200)])
    serial_number = StringField('Número de Série',
                                validators=[Optional(), Length(max=50)])
    warranty_end_date = DateField('Data de Término da Garantia',
                                  validators=[Optional()])
    status = SelectField('Status',
                         choices=[
                             ('active', 'Ativo'),
                             ('inactive', 'Inativo'),
                             ('maintenance', 'Em Manutenção')
                         ],
                         validators=[DataRequired()])
    notes = TextAreaField('Observações',
                          validators=[Optional(), Length(max=500)])
    submit = SubmitField('Salvar')

class MaintenancePlanForm(FlaskForm):
    equipment_id = SelectField('Equipamento',
                               coerce=int,
                               validators=[DataRequired(message='Selecione um equipamento')])
    name = StringField('Nome do Plano',
                       validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Descrição',
                                validators=[Optional(), Length(max=500)])
    frequency_days = IntegerField('Frequência (dias)',
                                  validators=[DataRequired(), NumberRange(min=1, max=365)])
    is_active = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar Plano')

class ChecklistItemForm(FlaskForm):
    description = StringField('Descrição da Tarefa',
                              validators=[DataRequired(), Length(max=200)])
    is_required = BooleanField('Obrigatório', default=True)
    order = HiddenField('Ordem')

class ChecklistTemplateForm(FlaskForm):
    maintenance_plan_id = SelectField('Plano de Manutenção',
                                      coerce=int,
                                      validators=[DataRequired()])
    name = StringField('Nome do Modelo',
                       validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descrição',
                                validators=[Optional(), Length(max=500)])
    items = FieldList(FormField(ChecklistItemForm), min_entries=1)
    submit = SubmitField('Salvar Modelo')

class MaintenanceScheduleForm(FlaskForm):
    equipment_id = SelectField('Equipamento',
                               coerce=int,
                               validators=[DataRequired(message='Selecione um equipamento')])
    maintenance_plan_id = SelectField('Plano de Manutenção',
                                      coerce=int,
                                      validators=[DataRequired(message='Selecione um plano')])
    scheduled_date = DateTimeField('Data Agendada',
                                   format='%Y-%m-%dT%H:%M',
                                   validators=[DataRequired(message='Informe a data e hora')])
    notes = TextAreaField('Observações',
                          validators=[Optional(), Length(max=500)])
    submit = SubmitField('Agendar')

    def validate_scheduled_date(self, field):
        if field.data <= datetime.now():
            raise ValidationError('A data agendada deve ser futura')

class ChecklistResultForm(FlaskForm):
    checklist_item_id = HiddenField('ID do Item', validators=[DataRequired()])
    status = SelectField('Status',
                         choices=[
                             ('ok', 'OK'),
                             ('nao_conforme', 'Não Conforme'),
                             ('nao_se_aplica', 'Não se Aplica'),
                             ('pendente', 'Pendente')
                         ],
                         validators=[DataRequired(message='Selecione um status')])
    notes = TextAreaField('Observações',
                          validators=[Optional(), Length(max=200)])
    arquivo = FileField('Anexar Arquivo',
                        validators=[
                            Optional(),
                            FileSize(max_size=5 * 1024 * 1024),
                            FileAllowed(['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xlsx'],
                                         'Apenas arquivos PDF, imagens e documentos são permitidos')
                        ])

    def validate_arquivo(self, field):
        if field.data:
            filename = field.data.filename
            if not ('.' in filename and
                    filename.rsplit('.', 1)[1].lower() in ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xlsx']):
                raise ValidationError('Tipo de arquivo não permitido')

class MaintenanceRecordForm(FlaskForm):
    equipment_id = HiddenField('ID do Equipamento', validators=[DataRequired()])
    schedule_id = HiddenField('ID do Agendamento', validators=[Optional()])
    start_time = DateTimeField('Início',
                               format='%Y-%m-%dT%H:%M',
                               validators=[DataRequired(message='Informe a data e hora de início')])
    end_time = DateTimeField('Término',
                             format='%Y-%m-%dT%H:%M',
                             validators=[Optional()])
    status = SelectField('Status',
                         choices=[
                             ('in_progress', 'Em Andamento'),
                             ('completed', 'Concluído'),
                             ('canceled', 'Cancelado')
                         ],
                         validators=[DataRequired(message='Selecione um status')])
    notes = TextAreaField('Observações Gerais',
                          validators=[Optional(), Length(max=500)])
    issues_found = TextAreaField('Problemas Encontrados',
                                 validators=[Optional(), Length(max=500)])
    actions_taken = TextAreaField('Ações Realizadas',
                                  validators=[Optional(), Length(max=500)])
    checklist_results = FieldList(
        FormField(ChecklistResultForm),
        min_entries=1,
        validators=[DataRequired(message='Adicione pelo menos um item ao checklist')]
    )
    submit = SubmitField('Salvar Registro')

    def validate_end_time(self, field):
        if field.data and field.data < self.start_time.data:
            raise ValidationError('A hora de término deve ser após a hora de início')
        if self.status.data == 'completed' and not field.data:
            raise ValidationError('Para manutenções concluídas, informe a hora de término')

class ReportForm(FlaskForm):
    start_date = DateField('Data Inicial',
                           validators=[DataRequired(message='Informe a data inicial')])
    end_date = DateField('Data Final',
                         validators=[DataRequired(message='Informe a data final')])
    equipment_id = SelectField('Equipamento',
                               coerce=int,
                               validators=[Optional()])
    technician_id = SelectField('Técnico',
                                coerce=int,
                                validators=[Optional()])
    status = SelectField('Status',
                         choices=[
                             ('all', 'Todos'),
                             ('completed', 'Concluído'),
                             ('pending', 'Pendente'),
                             ('in_progress', 'Em Andamento')
                         ],
                         validators=[Optional()])
    submit = SubmitField('Gerar Relatório')

    def validate_end_date(self, field):
        if field.data < self.start_date.data:
            raise ValidationError('A data final deve ser após a data inicial')

class ExportForm(FlaskForm):
    report_type = SelectField('Tipo de Relatório',
                              choices=[
                                  ('maintenance_history', 'Histórico de Manutenção'),
                                  ('equipment_status', 'Status dos Equipamentos'),
                                  ('technician_performance', 'Desempenho dos Técnicos')
                              ],
                              validators=[DataRequired()])
    start_date = DateField('Data Inicial',
                           validators=[DataRequired()])
    end_date = DateField('Data Final',
                         validators=[DataRequired()])
    submit = SubmitField('Exportar')

class DiarioManutencaoForm(FlaskForm):
    titulo = StringField('Título',
                         validators=[DataRequired(), Length(min=3, max=200)])
    conteudo = TextAreaField('Conteúdo',
                             validators=[DataRequired(), Length(max=2000)])
    equipment_id = SelectField('Equipamento (Opcional)',
                               coerce=int,
                               validators=[Optional()])
    arquivo = FileField('Anexar Arquivo (Opcional)',
                        validators=[
                            Optional(),
                            FileSize(max_size=5 * 1024 * 1024),
                            FileAllowed(['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xlsx'],
                                         'Apenas arquivos PDF, imagens e documentos são permitidos')
                        ])
    submit = SubmitField('Salvar')