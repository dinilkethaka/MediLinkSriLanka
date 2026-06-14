# app.py
# ---------------------------------------------------------
# This is the MAIN file that starts our Flask application.
#
# In Phase 1, this file's only job is to:
#   1. Create the Flask app
#   2. Load configuration from config.py
#   3. Connect our database (db) to the app
#   4. Create all tables (based on our models) if they don't exist yet
#   5. Give us one simple route to test that everything works
#
# In later phases, we will register "blueprints" (groups of routes)
# for admin, hospital, doctor, and auth here.
# ---------------------------------------------------------

from flask import Flask, jsonify
from flask_cors import CORS          # allows frontend (different origin) to call our API
from config import Config             # our settings file
from database.db import db             # our shared SQLAlchemy object

# Import all models so SQLAlchemy knows about every table
# before we call db.create_all()
from models import User, Hospital, Doctor, Patient, Prescription, SurgeryHistory


def create_app():
    """
    This function builds and configures our Flask app.

    WHY use a function instead of just writing code directly?
    This pattern is called the "Application Factory" pattern.
    It makes testing easier and avoids some import-order problems.
    For beginners: just know that calling create_app() gives us
    a fully configured Flask app, ready to run.
    """

    # Step 1: Create the Flask application object.
    # __name__ tells Flask where to find things like templates (we don't use any).
    app = Flask(__name__)

    # Step 2: Load our settings from config.py into the app.
    app.config.from_object(Config)

    # Step 3: Connect our shared "db" object to this specific app.
    # This is the step that actually links SQLAlchemy <-> Flask.
    db.init_app(app)

    # Step 4: Enable CORS (Cross-Origin Resource Sharing).
    # Our frontend (medilink_sl.html) might be opened from a different
    # "origin" (e.g. a file:// path or a different port) than our backend
    # (which runs on http://127.0.0.1:5000). Without CORS, browsers BLOCK
    # those requests for security reasons. This line allows them.
    CORS(app, supports_credentials=True)

    # Step 5: Create all database tables.
    # "app.app_context()" is required because Flask-SQLAlchemy needs to
    # know WHICH app it's working with when it talks to the database.
    with app.app_context():
        # db.create_all() looks at every model class we imported above
        # and creates a matching table in the database IF it doesn't
        # already exist. It will NOT delete or modify existing tables.
        db.create_all()
        print("✅ Database tables created (or already exist).")

    # Step 6: A simple test route.
    # Visiting http://127.0.0.1:5000/ in a browser should show this message.
    # This confirms our server is running correctly.
    @app.route("/")
    def index():
        return jsonify({
            "message": "MediLink backend is running!",
            "status": "ok"
        })

    # Return the fully configured app
    return app


# This block only runs if we execute "python app.py" directly
# (it will NOT run if this file is imported elsewhere).
if __name__ == "__main__":
    print("🚀 Starting MediLink Flask App...")  # ADD THIS
    app = create_app()
    app.run(debug=True)