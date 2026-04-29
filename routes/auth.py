from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app import mysql
from helpers import save_file
from config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role','')
        email = request.form.get('email','').strip()
        password = request.form.get('password','').strip()
        cur = mysql.connection.cursor()
        if role == 'admin':
            cur.execute("SELECT * FROM admin WHERE email=%s AND password=%s", (email, password))
            admin = cur.fetchone()
            cur.close()
            if admin:
                session.clear()
                session['admin'] = True
                session['admin_email'] = email
                return redirect(url_for('admin.dashboard'))
            flash('Invalid admin credentials.', 'danger')
        elif role in ('employer','employee'):
            cur.execute("SELECT * FROM users WHERE email=%s AND password=%s AND role=%s", (email, password, role))
            user = cur.fetchone()
            cur.close()
            if user:
                session.clear()
                session['user_id'] = user[0]
                session['name']    = user[1]
                session['role']    = user[6]
                session['image']   = user[7]
                return redirect(url_for('employer.profile') if role=='employer' else url_for('employee.profile'))
            flash('Invalid credentials.', 'danger')
        else:
            flash('Please select a role.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name     = request.form.get('name','').strip()
        gender   = request.form.get('gender','').strip()
        email    = request.form.get('email','').strip()
        phone    = request.form.get('phone','').strip()
        password = request.form.get('password','').strip()
        role     = request.form.get('role','').strip()
        image    = request.files.get('profile_image')
        if not all([name, gender, email, phone, password, role]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')
        img_file = save_file(image, Config.PROFILE_FOLDER, Config.ALLOWED_IMAGE_EXT) or 'default.png'
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users (name,gender,email,phone,password,role,profile_image) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (name,gender,email,phone,password,role,img_file))
            mysql.connection.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except:
            mysql.connection.rollback()
            flash('Email already registered.', 'danger')
        finally:
            cur.close()
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
