from flask import Blueprint, send_from_directory, session, redirect, url_for
from config import Config

shared_bp = Blueprint('shared', __name__)

@shared_bp.route('/attachment/<filename>')
def serve_attachment(filename):
    if not session.get('user_id') and not session.get('admin'):
        return redirect(url_for('auth.login'))
    return send_from_directory(Config.ATTACHMENT_FOLDER, filename)
