from flask import Flask, jsonify
from flask_cors import CORS # communicate frontend and backend when running on different ports
from flask_login import LoginManager
from config import Config
from database.db import db
from models import User, Hospital, Doctor, Patient, Prescription, SurgeryHistory #configure tables

#imports routes
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.hospital_routes import hospital_bp
from routes.doctor_routes import doctor_bp 

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app) # connect DB to flask
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

    #Identify / as homepage
    @app.route("/")
    def index():
        return jsonify({
            "message": "MediLink backend is running",
            "status": "ok"
        })

    return app


if __name__ == "__main__":
    print("Starting MediLink Flask App...")
    app = create_app()
    app.run(debug=True, ssl_context=('localhost+2.pem', 'localhost+2-key.pem'))


from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize the Application Firewall/Limiter
# It uses the remote IP address to track and block bad actors
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"] # Global traffic caps
)

def create_app():
    app = Flask(__name__)
    
    # Connect the firewall tool to your Flask application instance
    limiter.init_app(app)
    
    return app

# =========================================================
# PROTECTED LOGIN ROUTE (WITH CODE-BASED FIREWALL)
# =========================================================
@app.route('/api/login-step1', methods=['POST'])
# This firewall rule blocks an IP if they try to call login more than 5 times a minute
@limiter.limit("5 per minute", error_message="Firewall Block: Too many login attempts. Try again in a minute.")
def login_step1():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    
    # Your verification logic goes here...
    return jsonify({"status": "success", "message": "OTP code dispatched."})