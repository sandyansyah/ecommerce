from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import db
from app.models import User
from app.utils import validate_email, validate_password

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Validate form input
        if not email or not password:
            flash('Please enter both email and password', 'danger')
            return render_template('auth/login.html', title='Login')
        
        # Check if user exists and password is correct
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash('Invalid email or password', 'danger')
            return render_template('auth/login.html', title='Login')
        
        # Log in the user
        login_user(user, remember=remember)
        
        # Redirect to the page the user was trying to access, or home page
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.home')
        
        flash('You have been logged in successfully!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Login')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate form input
        if not all([username, email, password, confirm_password]):
            flash('Please fill out all fields', 'danger')
            return render_template('auth/register.html', title='Register')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html', title='Register')
        
        if not validate_email(email):
            flash('Please enter a valid email address', 'danger')
            return render_template('auth/register.html', title='Register')
        
        if not validate_password(password):
            flash('Password must be at least 8 characters long', 'danger')
            return render_template('auth/register.html', title='Register')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('auth/register.html', title='Register')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('auth/register.html', title='Register')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register')

@auth.route('/logout')
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.home'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page with update functionality"""
    if request.method == 'POST':
        # Update user profile information
        current_user.first_name = request.form.get('first_name', current_user.first_name)
        current_user.last_name = request.form.get('last_name', current_user.last_name)
        current_user.address = request.form.get('address', current_user.address)
        current_user.city = request.form.get('city', current_user.city)
        current_user.state = request.form.get('state', current_user.state)
        current_user.zip_code = request.form.get('zip_code', current_user.zip_code)
        current_user.phone = request.form.get('phone', current_user.phone)
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', title='My Profile')