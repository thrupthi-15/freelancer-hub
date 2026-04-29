from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from app import mysql

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id') or session.get('role') != 'employee':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# ---------- PROFILE ----------
@employee_bp.route('/profile')
@login_required
def profile():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    return render_template('employee/profile.html', user=user)

@employee_bp.route('/manage-profile', methods=['GET','POST'])
@login_required
def manage_profile():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        phone    = request.form.get('phone','').strip()
        password = request.form.get('password','').strip()
        cur.execute("UPDATE users SET phone=%s, password=%s WHERE id=%s", (phone, password, session['user_id']))
        mysql.connection.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('employee.profile'))
    cur.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    return render_template('employee/manage_profile.html', user=user)

# ---------- VIEW ALL OPEN POSTS ----------
@employee_bp.route('/view-posts')
@login_required
def view_posts():
    search = request.args.get('search','').strip()
    cur = mysql.connection.cursor()
    if search:
        like = f"%{search}%"
        cur.execute("""SELECT p.*, u.name as emp_name FROM projects p
                       JOIN users u ON p.employer_id=u.id
                       WHERE p.status='open' AND (p.title LIKE %s OR p.skills_required LIKE %s OR p.description LIKE %s)
                       ORDER BY p.posted_at DESC""", (like, like, like))
    else:
        cur.execute("""SELECT p.*, u.name as emp_name FROM projects p
                       JOIN users u ON p.employer_id=u.id
                       WHERE p.status='open' ORDER BY p.posted_at DESC""")
    projects = cur.fetchall()
    cur.close()
    return render_template('employee/view_posts.html', projects=projects, search=search)

# ---------- BID ON PROJECT ----------
@employee_bp.route('/bid/<int:pid>', methods=['GET','POST'])
@login_required
def bid_project(pid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM projects WHERE id=%s AND status='open'", (pid,))
    project = cur.fetchone()
    if not project:
        flash('Project not available.', 'danger')
        return redirect(url_for('employee.view_posts'))

    cur.execute("SELECT MIN(bid_amount) FROM bids WHERE project_id=%s", (pid,))
    lowest = cur.fetchone()[0] or 0

    if request.method == 'POST':
        amount = request.form.get('amount','').strip()
        try:
            cur.execute("""INSERT INTO bids (project_id, employee_id, bid_amount) VALUES (%s,%s,%s)
                           ON DUPLICATE KEY UPDATE bid_amount=%s""",
                        (pid, session['user_id'], amount, amount))
            mysql.connection.commit()
            flash('Bid submitted successfully!', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash('Error submitting bid.', 'danger')
        finally:
            cur.close()
        return redirect(url_for('employee.view_posts'))

    cur.close()
    return render_template('employee/bid_project.html', project=project, lowest=lowest)

# ---------- MY TASKS ----------
@employee_bp.route('/my-tasks')
@login_required
def my_tasks():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT at.id, p.title, p.description, p.skills_required, p.deadline,
               p.attachment, at.bid_amount, at.progress, at.assigned_at, u.name as employer_name
        FROM assigned_tasks at
        JOIN projects p ON at.project_id=p.id
        JOIN users u ON at.employer_id=u.id
        WHERE at.employee_id=%s
    """, (session['user_id'],))
    tasks = cur.fetchall()
    cur.close()
    return render_template('employee/my_tasks.html', tasks=tasks)

# ---------- UPDATE PROGRESS ----------
@employee_bp.route('/update-progress/<int:task_id>', methods=['GET','POST'])
@login_required
def update_progress(task_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        progress = request.form.get('progress','0')
        note     = request.form.get('note','')
        cur.execute("UPDATE assigned_tasks SET progress=%s, progress_note=%s WHERE id=%s AND employee_id=%s",
                    (progress, note, task_id, session['user_id']))
        mysql.connection.commit()
        flash('Progress updated!', 'success')
        cur.close()
        return redirect(url_for('employee.my_tasks'))
    cur.execute("""SELECT at.progress, at.progress_note, p.title
                   FROM assigned_tasks at JOIN projects p ON at.project_id=p.id
                   WHERE at.id=%s AND at.employee_id=%s""", (task_id, session['user_id']))
    task = cur.fetchone()
    cur.close()
    return render_template('employee/update_progress.html', task=task, task_id=task_id)

# ---------- VIEW PAYMENT ----------
@employee_bp.route('/view-payment/<int:task_id>')
@login_required
def view_payment(task_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT at.bid_amount, COALESCE(SUM(pay.amount),0) as total_received
        FROM assigned_tasks at
        LEFT JOIN payments pay ON pay.task_id=at.id
        WHERE at.id=%s AND at.employee_id=%s
        GROUP BY at.id
    """, (task_id, session['user_id']))
    info = cur.fetchone()
    cur.execute("SELECT * FROM payments WHERE task_id=%s ORDER BY paid_at DESC", (task_id,))
    history = cur.fetchall()
    cur.close()
    return render_template('employee/view_payment.html', info=info, history=history)

# ---------- VIDEO RESOURCES ----------
@employee_bp.route('/resources')
@login_required
def resources():
    search = request.args.get('search','').strip()
    cur = mysql.connection.cursor()
    if search:
        like = f"%{search}%"
        cur.execute("SELECT * FROM resources WHERE title LIKE %s OR skills LIKE %s ORDER BY uploaded_at DESC", (like, like))
    else:
        cur.execute("SELECT * FROM resources ORDER BY uploaded_at DESC")
    vids = cur.fetchall()
    cur.close()
    return render_template('employee/resources.html', resources=vids, search=search)
