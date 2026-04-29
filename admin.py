from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from app import mysql
from helpers import save_file
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE role='employer'")
    employers = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE role='employee'")
    employees = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM projects")
    projects = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM resources")
    res_count = cur.fetchone()[0]
    cur.close()
    return render_template('admin/dashboard.html',
                           employers=employers, employees=employees,
                           projects=projects, res_count=res_count)

@admin_bp.route('/add-resource', methods=['GET','POST'])
@admin_required
def add_resource():
    if request.method == 'POST':
        title  = request.form.get('title','').strip()
        skills = request.form.get('skills','').strip()
        video  = request.files.get('video_file')
        vid_file = save_file(video, Config.VIDEO_FOLDER, Config.ALLOWED_VIDEO_EXT)
        if not vid_file:
            flash('Please upload a valid video file (mp4, avi, mov, mkv, webm).', 'danger')
            return render_template('admin/add_resource.html')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO resources (title,skills,video_file) VALUES (%s,%s,%s)", (title,skills,vid_file))
        mysql.connection.commit()
        cur.close()
        flash('Resource posted successfully!', 'success')
        return redirect(url_for('admin.view_resources'))
    return render_template('admin/add_resource.html')

@admin_bp.route('/view-resources')
@admin_required
def view_resources():
    search = request.args.get('search','').strip()
    cur = mysql.connection.cursor()
    if search:
        like = f"%{search}%"
        cur.execute("SELECT * FROM resources WHERE title LIKE %s OR skills LIKE %s ORDER BY uploaded_at DESC", (like,like))
    else:
        cur.execute("SELECT * FROM resources ORDER BY uploaded_at DESC")
    resources = cur.fetchall()
    cur.close()
    return render_template('admin/view_resources.html', resources=resources, search=search)

@admin_bp.route('/delete-resource/<int:rid>')
@admin_required
def delete_resource(rid):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM resources WHERE id=%s", (rid,))
    mysql.connection.commit()
    cur.close()
    flash('Resource deleted.', 'success')
    return redirect(url_for('admin.view_resources'))
