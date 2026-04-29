from flask import Flask, redirect, url_for
from flask_mysqldb import MySQL
import os
from config import Config

mysql = MySQL()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mysql.init_app(app)

    os.makedirs(Config.PROFILE_FOLDER,    exist_ok=True)
    os.makedirs(Config.ATTACHMENT_FOLDER, exist_ok=True)
    os.makedirs(Config.VIDEO_FOLDER,      exist_ok=True)

    from routes.auth     import auth_bp
    from routes.employer import employer_bp
    from routes.employee import employee_bp
    from routes.admin    import admin_bp
    from routes.shared   import shared_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(employer_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(shared_bp)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)