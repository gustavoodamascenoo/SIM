from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, FloatField, TextAreaField, SelectField
from wtforms import BooleanField, IntegerField, DateTimeField, HiddenField, FieldList, FormField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[Optional()])
    role = SelectField('Role', choices=[
        ('technician', 'Technician'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Administrator')
    ], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class EquipmentForm(FlaskForm):
    identification_number = StringField('Identification Number', validators=[DataRequired()])
    model = StringField('Model', validators=[DataRequired()])
    manufacturer = StringField('Manufacturer', validators=[DataRequired()])
    power = FloatField('Power (kW)', validators=[DataRequired(), NumberRange(min=0)])
    installation_date = DateField('Installation Date', validators=[DataRequired()])
    location_building = StringField('Building', validators=[DataRequired()])
    location_floor = IntegerField('Floor', validators=[DataRequired()])
    location_room = StringField('Room', validators=[DataRequired()])
    location_details = StringField('Location Details', validators=[Optional()])
    serial_number = StringField('Serial Number', validators=[Optional()])
    warranty_end_date = DateField('Warranty End Date', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Submit')

class MaintenancePlanForm(FlaskForm):
    equipment_id = SelectField('Equipment', coerce=int, validators=[DataRequired()])
    name = StringField('Plan Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    frequency_days = IntegerField('Frequency (days)', validators=[DataRequired(), NumberRange(min=1)])
    is_active = BooleanField('Active')
    submit = SubmitField('Submit')

class ChecklistItemForm(FlaskForm):
    description = StringField('Task Description', validators=[DataRequired()])
    is_required = BooleanField('Required', default=True)
    order = HiddenField('Order')

class ChecklistTemplateForm(FlaskForm):
    maintenance_plan_id = SelectField('Maintenance Plan', coerce=int, validators=[DataRequired()])
    name = StringField('Template Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    items = FieldList(FormField(ChecklistItemForm), min_entries=1)
    add_item = SubmitField('Add Item')
    submit = SubmitField('Submit')

class MaintenanceScheduleForm(FlaskForm):
    equipment_id = SelectField('Equipment', coerce=int, validators=[DataRequired()])
    maintenance_plan_id = SelectField('Maintenance Plan', coerce=int, validators=[DataRequired()])
    scheduled_date = DateTimeField('Scheduled Date', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Schedule Maintenance')

class ChecklistResultForm(FlaskForm):
    checklist_item_id = HiddenField('Checklist Item ID')
    status = SelectField('Status', choices=[
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('not_applicable', 'Not Applicable')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])

class MaintenanceRecordForm(FlaskForm):
    equipment_id = HiddenField('Equipment ID')
    schedule_id = HiddenField('Schedule ID')
    start_time = DateTimeField('Start Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    end_time = DateTimeField('End Time', format='%Y-%m-%d %H:%M', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    issues_found = TextAreaField('Issues Found', validators=[Optional()])
    actions_taken = TextAreaField('Actions Taken', validators=[Optional()])
    checklist_results = FieldList(FormField(ChecklistResultForm))
    submit = SubmitField('Submit')

class ReportForm(FlaskForm):
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    equipment_id = SelectField('Equipment', coerce=int, validators=[Optional()])
    technician_id = SelectField('Technician', coerce=int, validators=[Optional()])
    status = SelectField('Status', choices=[
        ('all', 'All'),
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress')
    ], validators=[Optional()])
    submit = SubmitField('Generate Report')

class ExportForm(FlaskForm):
    report_type = SelectField('Report Type', choices=[
        ('maintenance_history', 'Maintenance History'),
        ('equipment_status', 'Equipment Status'),
        ('technician_performance', 'Technician Performance')
    ], validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    submit = SubmitField('Export to CSV')
