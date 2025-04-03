from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from models import User
from forms import LoginForm, RegistrationForm

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
def index():
    """Redirect to login page if not logged in, otherwise to dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('maintenance.dashboard'))
    return redirect(url_for('users.login'))

@users_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('maintenance.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('maintenance.dashboard'))
        else:
            flash('Login failed. Please check username and password.', 'danger')
    
    return render_template('login.html', form=form)

@users_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('users.login'))

@users_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register new users (admin only)"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('maintenance.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('users.user_list'))
    
    return render_template('register.html', form=form)

@users_bp.route('/users')
@login_required
def user_list():
    """Display list of all users (admin only)"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('maintenance.dashboard'))
    
    users = User.query.all()
    return render_template('users/index.html', users=users)

@users_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit user details (admin only)"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('maintenance.dashboard'))
    
    user = User.query.get_or_404(user_id)
    form = RegistrationForm(obj=user)
    
    # Don't validate password for edits
    if request.method == 'POST':
        if form.password.data.strip() == '':
            del form.password
            del form.confirm_password
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.role = form.role.data
        
        if form.password.data and form.password.data.strip() != '':
            user.set_password(form.password.data)
        
        db.session.commit()
        flash(f'User {user.username} has been updated!', 'success')
        return redirect(url_for('users.user_list'))
    
    return render_template('users/edit.html', form=form, user=user)

@users_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user (admin only)"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('maintenance.dashboard'))
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('users.user_list'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted!', 'success')
    return redirect(url_for('users.user_list'))

@users_bp.route('/profile')
@login_required
def profile():
    """Display user profile"""
    return render_template('users/profile.html', user=current_user)
