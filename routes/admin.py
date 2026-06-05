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

# ── NEW: Employer detail list ──────────────────────────────────────────────────
@admin_bp.route('/employers')
@admin_required
def list_employers():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, email, created_at FROM users WHERE role='employer' ORDER BY created_at DESC")
    employers = cur.fetchall()
    cur.close()
    return render_template('admin/list_employers.html', employers=employers)

# ── NEW: Employee detail list ──────────────────────────────────────────────────
@admin_bp.route('/employees')
@admin_required
def list_employees():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, email, created_at FROM users WHERE role='employee' ORDER BY created_at DESC")
    employees = cur.fetchall()
    cur.close()
    return render_template('admin/list_employees.html', employees=employees)

# ── NEW: Projects detail list ──────────────────────────────────────────────────
@admin_bp.route('/projects')
@admin_required
def list_projects():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            p.id,
            p.title,
            p.budget,
            p.status,
            p.created_at,
            poster.name   AS poster_name,
            poster.email  AS poster_email,
            worker.name   AS worker_name,
            worker.email  AS worker_email
        FROM projects p
        JOIN users poster ON poster.id = p.employer_id
        LEFT JOIN users worker ON worker.id = p.assigned_to
        ORDER BY p.created_at DESC
    """)
    projects = cur.fetchall()
    cur.close()
    return render_template('admin/list_projects.html', projects=projects)

# ── NEW: Resources detail list ─────────────────────────────────────────────────
@admin_bp.route('/resources-list')
@admin_required
def list_resources():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, title, skills, video_file, uploaded_at FROM resources ORDER BY uploaded_at DESC")
    resources = cur.fetchall()
    cur.close()
    return render_template('admin/list_resources.html', resources=resources)

# ── Existing routes below (unchanged) ─────────────────────────────────────────
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
