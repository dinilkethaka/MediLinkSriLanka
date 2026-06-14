# app.py
# PHASE 4 CHANGES:
#   - Import hospital_bp
#   - Register hospital_bp
# Everything else unchanged from Phase 3.

from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager

from config import Config
from database.db import db

from models import User, Hospital, Doctor, Patient, Prescription, SurgeryHistory

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.hospital_routes import hospital_bp  # PHASE 4


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app, supports_credentials=True)

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"error": "Unauthorized: please log in"}), 401

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(hospital_bp)  # PHASE 4

    with app.app_context():
        db.create_all()
        print("✅ Database tables created (or already exist).")

    @app.route("/")
    def index():
        return jsonify({
            "message": "MediLink backend is running!",
            "status": "ok"
        })

    return app


if __name__ == "__main__":
    print("🚀 Starting MediLink Flask App...")
    app = create_app()
    app.run(debug=True)