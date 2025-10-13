# app/auth.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User  # We will create this models.py file next
from . import db, bcrypt # We will set up this import structure

# 1. Create the Blueprint
# The first argument, 'auth', is the name of the blueprint.
# The second argument, __name__, is the import name of the blueprint's package.
# The third argument, template_folder, tells the blueprint where to find its templates.
auth_bp = Blueprint('auth', __name__)

# 2. Define the Routes for this Blueprint

@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Invalid username or password. Please try again.', 'danger')
            return redirect(url_for('auth.signin'))

        login_user(user, remember=remember)
        flash(f'Welcome back, {user.username}!', 'success')
        
        # Redirect to the main index page after successful login
        return redirect(url_for('settings.academic_settings'))

    return render_template('signin.html')


@auth_bp.route('/signout')
@login_required
def signout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('auth.signin'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.username = request.form.get('username')
        email = request.form.get('email') or None
        current_user.email = email
        
        password = request.form.get('password')
        if password:
            current_user.set_password(password)
            
        db.session.commit()
        flash('Your profile has been updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('profile.html', user=current_user)


@auth_bp.route('/admins')
@login_required
def admins():
    all_users = User.query.order_by(User.username).all()
    return render_template('admins.html', all_users=all_users)


@auth_bp.route('/add_user', methods=['POST'])
@login_required
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email') or None

    if User.query.filter_by(username=username).first():
        flash(f"Username '{username}' already exists.", 'danger')
        return redirect(url_for('auth.admins'))

    if email and User.query.filter_by(email=email).first():
        flash(f"Email '{email}' is already registered.", 'danger')
        return redirect(url_for('auth.admins'))

    new_user = User(username=username, email=email)
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()

    flash(f"User '{username}' created successfully!", 'success')
    return redirect(url_for('auth.admins'))


@auth_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash("You cannot delete your own account.", 'danger')
        return redirect(url_for('auth.admins'))

    user_to_delete = User.query.get_or_404(user_id)
    db.session.delete(user_to_delete)
    db.session.commit()
    
    flash(f"User '{user_to_delete.username}' has been deleted.", 'success')
    return redirect(url_for('auth.admins'))

