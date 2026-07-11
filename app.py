from flask import Flask, jsonify
from flask_cors import CORS # communicate frontend and backend when running on different ports
from flask_login import LoginManager
from config import Config
from database.db import db
from models import User, Hospital, Doctor, Patient, Prescription, SurgeryHistory #configure tables
from extensions import mail
from apscheduler.schedulers.background import BackgroundScheduler  # BACKUP
import atexit

#imports routes
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.hospital_routes import hospital_bp
from routes.doctor_routes import doctor_bp 


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app) # connect DB to flask
    mail.init_app(app)
    CORS(app, supports_credentials=True)

    login_manager = LoginManager()
    login_manager.init_app(app)
    

    #access without login
    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"error": "Unauthorized: please log in"}), 401
    
    #If user refresh page 
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(hospital_bp)
    app.register_blueprint(doctor_bp)  

    #create tables
    with app.app_context():
        db.create_all()
        print("Database tables created (or already exist).")


    # Weekly backup
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        func=_scheduled_backup,
        trigger='cron',
        day_of_week='sun',
        hour=1,
        minute=0,
        id='weekly_backup',
        name='Weekly Google Drive Backup',
        replace_existing=True
    )

    scheduler.start()
    print("Weekly backup scheduler started (every Sunday at 1:00 AM).")

    atexit.register(lambda: scheduler.shutdown())
    
    #Identify / as homepage
    @app.route("/")
    def index():
        return jsonify({
            "message": "MediLink backend is running",
            "status": "ok"
        })

    return app

def _scheduled_backup():
    """
    Called automatically by APScheduler every Sunday at 1 AM.
    Runs outside a Flask request context.
    """
    from services.backup_service import run_backup
    print("Running scheduled weekly backup...")
    result = run_backup()
    if result["success"]:
        print(f"Weekly backup completed: {result['filename']}")
    else:
        print(f"Weekly backup FAILED: {result['message']}")

if __name__ == "__main__":
    print("Starting MediLink Flask App...")
    app = create_app()
    app.run(debug=True, ssl_context=('localhost+2.pem', 'localhost+2-key.pem'))
