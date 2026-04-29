from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_from_directory
from functools import wraps
from app import mysql
from helpers import save_file
from config import Config

employer_bp = Blueprint('employer', __name__, url_prefix='/employer')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id') or session.get('role') != 'employer':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# ---------- PROFILE ----------
@employer_bp.route('/profile')
@login_required
def profile():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    return render_template('employer/profile.html', user=user)

@employer_bp.route('/manage-profile', methods=['GET','POST'])
@login_required
def manage_profile():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        phone    = request.form.get('phone','').strip()
        password = request.form.get('password','').strip()
        cur.execute("UPDATE users SET phone=%s, password=%s WHERE id=%s", (phone, password, session['user_id']))
        mysql.connection.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('employer.profile'))
    cur.execute("SELECT * FROM users WHERE id=%s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    return render_template('employer/manage_profile.html', user=user)

# ---------- POST PROJECT ----------
@employer_bp.route('/post-project', methods=['GET','POST'])
@login_required
def post_project():
    if request.method == 'POST':
        title    = request.form.get('title','').strip()
        desc     = request.form.get('description','').strip()
        skills   = request.form.get('skills','').strip()
        budget   = request.form.get('budget','').strip()
        deadline = request.form.get('deadline','').strip()
        pdf      = request.files.get('attachment')
        pdf_file = save_file(pdf, Config.ATTACHMENT_FOLDER, Config.ALLOWED_PDF_EXT)
        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO projects (employer_id,title,description,skills_required,budget,deadline,attachment)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (session['user_id'], title, desc, skills, budget, deadline, pdf_file))
        mysql.connection.commit()
        cur.close()
        flash('Project posted successfully!', 'success')
        return redirect(url_for('employer.view_posts'))
    return render_template('employer/post_project.html')

# ---------- VIEW MY POSTS ----------
@employer_bp.route('/view-posts')
@login_required
def view_posts():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM projects WHERE employer_id=%s ORDER BY posted_at DESC", (session['user_id'],))
    projects = cur.fetchall()
    cur.close()
    return render_template('employer/view_posts.html', projects=projects)

# ---------- DELETE PROJECT ----------
@employer_bp.route('/delete-project/<int:pid>')
@login_required
def delete_project(pid):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM projects WHERE id=%s AND employer_id=%s", (pid, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash('Project deleted.', 'success')
    return redirect(url_for('employer.view_posts'))

# ---------- VIEW BIDS ----------
@employer_bp.route('/view-bids/<int:pid>')
@login_required
def view_bids(pid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM projects WHERE id=%s AND employer_id=%s", (pid, session['user_id']))
    project = cur.fetchone()
    # Get lowest bid per employee
    cur.execute("""
        SELECT u.id, u.name, u.gender, u.email, u.phone, u.profile_image, b.bid_amount, b.id as bid_id
        FROM bids b JOIN users u ON b.employee_id=u.id
        WHERE b.project_id=%s
        ORDER BY b.bid_amount ASC
    """, (pid,))
    bids = cur.fetchall()
    cur.close()
    return render_template('employer/view_bids.html', project=project, bids=bids)

# ---------- ASSIGN TASK ----------
@employer_bp.route('/assign-task/<int:pid>/<int:emp_id>')
@login_required
def assign_task(pid, emp_id):
    cur = mysql.connection.cursor()
    # Get lowest bid amount for this employee on this project
    cur.execute("SELECT bid_amount FROM bids WHERE project_id=%s AND employee_id=%s", (pid, emp_id))
    bid = cur.fetchone()
    if not bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('employer.view_bids', pid=pid))
    try:
        cur.execute("""INSERT INTO assigned_tasks (project_id,employee_id,employer_id,bid_amount)
                       VALUES (%s,%s,%s,%s)""", (pid, emp_id, session['user_id'], bid[0]))
        cur.execute("UPDATE projects SET status='assigned' WHERE id=%s", (pid,))
        mysql.connection.commit()
        flash('Task assigned successfully!', 'success')
    except:
        mysql.connection.rollback()
        flash('Task already assigned.', 'danger')
    finally:
        cur.close()
    return redirect(url_for('employer.view_assigned'))

# ---------- VIEW ASSIGNED TASKS ----------
@employer_bp.route('/assigned-tasks')
@login_required
def view_assigned():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT at.id, p.title, p.description, p.skills_required, p.budget, p.deadline, p.attachment,
               p.posted_at, u.name, u.email, u.phone, at.bid_amount, at.progress, at.assigned_at
        FROM assigned_tasks at
        JOIN projects p ON at.project_id=p.id
        JOIN users u ON at.employee_id=u.id
        WHERE at.employer_id=%s
        ORDER BY at.assigned_at DESC
    """, (session['user_id'],))
    tasks = cur.fetchall()
    cur.close()
    return render_template('employer/assigned_tasks.html', tasks=tasks)

# ---------- VIEW STATUS ----------
@employer_bp.route('/view-status/<int:task_id>')
@login_required
def view_status(task_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT at.progress, at.progress_note, p.title, u.name
        FROM assigned_tasks at
        JOIN projects p ON at.project_id=p.id
        JOIN users u ON at.employee_id=u.id
        WHERE at.id=%s AND at.employer_id=%s
    """, (task_id, session['user_id']))
    task = cur.fetchone()
    cur.close()
    return render_template('employer/view_status.html', task=task, task_id=task_id)

# ---------- PAYMENT ----------
@employer_bp.route('/payment/<int:task_id>', methods=['GET','POST'])
@login_required
def payment(task_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        from_upi = request.form.get('from_upi','').strip()
        to_upi   = request.form.get('to_upi','').strip()
        amount   = request.form.get('amount','').strip()
        cur.execute("INSERT INTO payments (task_id,from_upi,to_upi,amount) VALUES (%s,%s,%s,%s)",
                    (task_id, from_upi, to_upi, amount))
        mysql.connection.commit()
        cur.close()
        flash('Payment successful!', 'success')
        return redirect(url_for('employer.payment', task_id=task_id))

    cur.execute("""
        SELECT at.bid_amount, COALESCE(SUM(pay.amount),0) as total_paid, at.employer_id
        FROM assigned_tasks at
        LEFT JOIN payments pay ON pay.task_id=at.id
        WHERE at.id=%s
        GROUP BY at.id
    """, (task_id,))
    info = cur.fetchone()
    cur.execute("SELECT * FROM payments WHERE task_id=%s ORDER BY paid_at DESC", (task_id,))
    history = cur.fetchall()
    cur.close()
    return render_template('employer/payment.html', info=info, history=history, task_id=task_id)

# ---------- SERVE ATTACHMENT ----------
@employer_bp.route('/attachment/<filename>')
@login_required
def serve_attachment(filename):
    return send_from_directory(Config.ATTACHMENT_FOLDER, filename)
