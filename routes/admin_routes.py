# routes/admin_routes.py
# ---------------------------------------------------------
# This file defines all routes for the ADMIN role:
#
#   Hospitals:
#     GET  /api/admin/hospitals          -> list all hospitals
#     POST /api/admin/hospitals          -> add a new hospital
#     GET  /api/admin/hospitals/<id>     -> view one hospital
#
#   Doctors:
#     GET  /api/admin/doctors            -> list all doctors
#     POST /api/admin/doctors            -> add a new doctor
#     GET  /api/admin/doctors/<id>       -> view one doctor
#
#   Patients:
#     GET  /api/admin/patients           -> list ALL patients (system-wide)
#     GET  /api/admin/patients/<id>      -> view one patient
#     POST /api/admin/patients/import-csv -> bulk import patients from CSV (Phase 6)
#
#   Dashboard:
#     GET  /api/admin/dashboard          -> stats for the admin dashboard
#
# EVERY route here requires:
#   @login_required          -> must be logged in
#   @role_required("admin")  -> AND must have role == "admin"
# ---------------------------------------------------------

from flask import Blueprint, request, jsonify
from flask_login import login_required

from database.db import db
from services.authentication_service import role_required
from services.csv_import_service import import_patients_from_csv  # PHASE 6

from models.hospital import Hospital
from models.doctor import Doctor
from models.patient import Patient
from models.prescription import Prescription
from models.user import User


# Create the blueprint for all admin routes.
admin_bp = Blueprint("admin", __name__)


# =====================================================
# HOSPITALS
# =====================================================

@admin_bp.route("/api/admin/hospitals", methods=["GET"])
@login_required
@role_required("admin")
def list_hospitals():
    """
    Returns a list of ALL hospitals in the system.

    The frontend's "Hospital Registry" table and the chips
    ("All / Government / Private") use this data.
    """

    # Hospital.query.all() runs: SELECT * FROM hospital
    # and gives us a Python list of Hospital objects.
    hospitals = Hospital.query.all()

    # We convert each Hospital object into a dictionary using
    # the to_dict() method we wrote in Phase 1, then wrap the
    # whole list in JSON.
    return jsonify({
        "hospitals": [h.to_dict() for h in hospitals]
    }), 200


@admin_bp.route("/api/admin/hospitals", methods=["POST"])
@login_required
@role_required("admin")
def add_hospital():
    """
    Adds a new hospital to the system.

    Expects JSON body, matching the "Register New Hospital" modal
    in the frontend:
        {
            "hospital_name": "Ratnapura General Hospital",
            "hospital_type": "Government",   <- must be "Government" or "Private"
            "province": "Sabaragamuwa Province",
            "city": "Ratnapura",
            "address": "Main Street, Ratnapura",
            "bed_capacity": 500,
            "contact_number": "0452222222",
            "email": "admin@ratnapura.gov.lk"
        }

    Returns the new hospital's ID on success.
    """

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # --- INPUT VALIDATION ---
    # "Required" fields - if these are missing, we reject the request
    # BEFORE touching the database. This prevents bad/incomplete data.
    hospital_name = data.get("hospital_name")
    hospital_type = data.get("hospital_type")

    if not hospital_name:
        return jsonify({"error": "hospital_name is required"}), 400

    if hospital_type not in ("Government", "Private"):
        return jsonify({"error": "hospital_type must be 'Government' or 'Private'"}), 400

    # Check for duplicate hospital name (optional, but good practice -
    # prevents accidentally registering the same hospital twice).
    existing = Hospital.query.filter_by(hospital_name=hospital_name).first()
    if existing:
        return jsonify({"error": "A hospital with this name already exists"}), 409
        # 409 Conflict = "this request conflicts with existing data"

    # --- CREATE THE NEW HOSPITAL ---
    # .get() with no second argument returns None if the key is missing,
    # which is fine for "optional" fields like address, email, etc.
    new_hospital = Hospital(
        hospital_name=hospital_name,
        hospital_type=hospital_type,
        province=data.get("province"),
        city=data.get("city"),
        address=data.get("address"),
        bed_capacity=data.get("bed_capacity", 0),  # default to 0 if not provided
        contact_number=data.get("contact_number"),
        email=data.get("email")
    )

    # db.session.add() stages this new row for insertion.
    db.session.add(new_hospital)

    # db.session.commit() actually saves it to the database.
    # After commit(), new_hospital.id is automatically filled in
    # by the database (auto-increment).
    db.session.commit()

    return jsonify({
        "message": "Hospital registered successfully",
        "hospital": new_hospital.to_dict()
    }), 201
    # 201 Created = "a new resource was successfully created"


@admin_bp.route("/api/admin/hospitals/<int:hospital_id>", methods=["GET"])
@login_required
@role_required("admin")
def get_hospital(hospital_id):
    """
    Returns details for ONE specific hospital, by its ID.

    <int:hospital_id> in the URL means Flask will automatically
    convert that part of the URL into an integer and pass it
    as the "hospital_id" argument to this function.

    Example: GET /api/admin/hospitals/3  -> hospital_id = 3
    """

    # Hospital.query.get(id) is a shortcut for:
    #   SELECT * FROM hospital WHERE id = :id
    # It returns None if no hospital with that ID exists.
    hospital = Hospital.query.get(hospital_id)

    if hospital is None:
        return jsonify({"error": "Hospital not found"}), 404

    return jsonify({"hospital": hospital.to_dict()}), 200


# =====================================================
# DOCTORS
# =====================================================

@admin_bp.route("/api/admin/doctors", methods=["GET"])
@login_required
@role_required("admin")
def list_doctors():
    """
    Returns a list of ALL doctors in the system.
    Used by the "Doctor Registry" table in the Admin dashboard.
    """
    doctors = Doctor.query.all()
    return jsonify({
        "doctors": [d.to_dict() for d in doctors]
    }), 200


@admin_bp.route("/api/admin/doctors", methods=["POST"])
@login_required
@role_required("admin")
def add_doctor():
    """
    Adds a new doctor's professional profile AND creates a login
    account for them (role = "doctor").

    Expects JSON body, matching the "Register New Doctor" modal:
        {
            "doctor_name": "Dr. Nimal Perera",
            "nic": "902501234V",
            "license_number": "SLMC-12345",
            "specialization": "Cardiology",
            "hospital_id": 1,
            "phone_number": "0771234567",
            "email": "nimal.perera@medilink.lk",   <- needed for login
            "username": "doctor_nimal",            <- needed for login
            "password": "SomePassword123"          <- needed for login
        }

    WHY create BOTH a Doctor row AND a User row?
    - Doctor row = professional details (shown in tables, used for
      prescriptions/medical records)
    - User row = login credentials (used by /api/auth/login)

    They are linked via User.doctor_id -> Doctor.id
    """

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # --- VALIDATE REQUIRED FIELDS ---
    doctor_name = data.get("doctor_name")
    license_number = data.get("license_number")
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")

    # We check all "must-have" fields in one go. If any are missing,
    # we list out exactly which ones in the error message - this
    # helps beginners debugging their frontend forms.
    missing = []
    if not doctor_name:
        missing.append("doctor_name")
    if not license_number:
        missing.append("license_number")
    if not email:
        missing.append("email")
    if not username:
        missing.append("username")
    if not password:
        missing.append("password")

    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # --- CHECK FOR DUPLICATES ---
    # license_number must be unique (enforced by the database too,
    # but checking here first lets us give a friendlier error message).
    if Doctor.query.filter_by(license_number=license_number).first():
        return jsonify({"error": "A doctor with this license number already exists"}), 409

    if Doctor.query.filter_by(email=email).first():
        return jsonify({"error": "A doctor with this email already exists"}), 409

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "This username is already taken"}), 409

    # If a hospital_id was provided, make sure that hospital actually exists.
    hospital_id = data.get("hospital_id")
    if hospital_id is not None:
        hospital = Hospital.query.get(hospital_id)
        if hospital is None:
            return jsonify({"error": f"No hospital found with id {hospital_id}"}), 404

    # --- CREATE THE DOCTOR PROFILE ---
    new_doctor = Doctor(
        doctor_name=doctor_name,
        specialization=data.get("specialization"),
        license_number=license_number,
        email=email,
        phone_number=data.get("phone_number"),
        nic=data.get("nic"),
        hospital_id=hospital_id
    )
    db.session.add(new_doctor)

    # flush() sends the INSERT now so new_doctor.id is filled in,
    # WITHOUT fully committing yet. We need new_doctor.id for the
    # User row below.
    db.session.flush()

    # --- CREATE THE LOGIN ACCOUNT (User row) ---
    new_user = User(
        username=username,
        role="doctor",
        full_name=doctor_name,
        email=email,
        phone_number=data.get("phone_number"),
        doctor_id=new_doctor.id  # link this login to the doctor profile above
    )
    new_user.set_password(password)  # hash the password before storing
    db.session.add(new_user)

    # Now commit BOTH new rows (Doctor + User) together.
    # If anything failed partway through, db.session.rollback() (not
    # shown here, but Flask-SQLAlchemy handles this automatically on
    # error) would undo everything - so we never end up with a Doctor
    # row but no matching User row.
    db.session.commit()

    return jsonify({
        "message": "Doctor registered successfully",
        "doctor": new_doctor.to_dict()
    }), 201


@admin_bp.route("/api/admin/doctors/<int:doctor_id>", methods=["GET"])
@login_required
@role_required("admin")
def get_doctor(doctor_id):
    """Returns details for ONE specific doctor, by ID."""
    doctor = Doctor.query.get(doctor_id)

    if doctor is None:
        return jsonify({"error": "Doctor not found"}), 404

    return jsonify({"doctor": doctor.to_dict()}), 200


# =====================================================
# PATIENTS (system-wide, admin can view but not add manually)
# =====================================================

@admin_bp.route("/api/admin/patients", methods=["GET"])
@login_required
@role_required("admin")
def list_all_patients():
    """
    Returns ALL patients in the system, from every hospital.

    NOTE: Admins can VIEW patients but, per the project requirements,
    only HOSPITALS can REGISTER new patients one-by-one (that route
    lives in hospital_routes.py from Phase 4). Admins can however
    BULK IMPORT patients via CSV (see import_patients_csv below).

    Supports an optional search query string:
        GET /api/admin/patients?search=Perera

    This searches both the patient's name and NIC.
    """

    # request.args.get("search") reads a URL query parameter.
    # Example URL: /api/admin/patients?search=kasun
    # request.args.get("search") would return "kasun"
    search = request.args.get("search", "").strip()

    if search:
        # We search in first_name, last_name, OR nic.
        # ilike() means "case-insensitive LIKE" - so searching "kasun"
        # will also match "Kasun".
        # The % symbols mean "anything can come before/after this text".
        search_pattern = f"%{search}%"

        patients = Patient.query.filter(
            db.or_(
                Patient.first_name.ilike(search_pattern),
                Patient.last_name.ilike(search_pattern),
                Patient.nic.ilike(search_pattern)
            )
        ).all()
    else:
        # No search term provided - return everyone.
        patients = Patient.query.all()

    return jsonify({
        "patients": [p.to_dict() for p in patients]
    }), 200


@admin_bp.route("/api/admin/patients/<int:patient_id>", methods=["GET"])
@login_required
@role_required("admin")
def get_patient(patient_id):
    """Returns details for ONE specific patient, by ID."""
    patient = Patient.query.get(patient_id)

    if patient is None:
        return jsonify({"error": "Patient not found"}), 404

    return jsonify({"patient": patient.to_dict()}), 200


# =====================================================
# CSV IMPORT (Phase 6)
# =====================================================

@admin_bp.route("/api/admin/patients/import-csv", methods=["POST"])
@login_required
@role_required("admin")
def import_patients_csv():
    """
    Bulk-imports patients from an uploaded CSV file.

    This is a "multipart/form-data" request (a file upload), NOT JSON!
    The frontend's upload zone sends:
      - a file (key: "file")
      - a hospital_id (key: "hospital_id") - which hospital these
        patients should be linked to

    Example using curl:
        curl -X POST http://127.0.0.1:5000/api/admin/patients/import-csv \\
             -F "file=@patients.csv" \\
             -F "hospital_id=1"

    Returns a summary of the import (see services/csv_import_service.py).
    """

    # --- STEP 1: Check a file was actually uploaded ---
    # request.files is a dictionary-like object containing uploaded
    # files, keyed by the form field name ("file" in our case).
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Expected a form field named 'file'."}), 400

    file = request.files["file"]

    # If the user submitted the form without choosing a file,
    # file.filename will be an empty string.
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # --- STEP 2: Check the file extension ---
    # We only accept .csv files for now (the frontend also mentions
    # .xlsx, but reading Excel files requires an extra library -
    # we can add that in a later phase if needed).
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only .csv files are supported"}), 400

    # --- STEP 3: Get and validate hospital_id ---
    # request.form is used for regular form fields sent alongside
    # the file (as opposed to request.get_json() which is for
    # pure JSON requests).
    hospital_id_raw = request.form.get("hospital_id")

    hospital_id = None
    if hospital_id_raw:
        try:
            hospital_id = int(hospital_id_raw)
        except ValueError:
            return jsonify({"error": "hospital_id must be a number"}), 400

        # Make sure this hospital actually exists.
        hospital = Hospital.query.get(hospital_id)
        if hospital is None:
            return jsonify({"error": f"No hospital found with id {hospital_id}"}), 404

    # --- STEP 4: Run the import using our service function ---
    summary = import_patients_from_csv(file, hospital_id)

    return jsonify({
        "message": "CSV import completed",
        "summary": summary
    }), 200


# =====================================================
# DASHBOARD STATS
# =====================================================

@admin_bp.route("/api/admin/dashboard", methods=["GET"])
@login_required
@role_required("admin")
def admin_dashboard():
    """
    Returns the numbers shown on the Admin Dashboard's stat boxes:
      - Total Patients
      - Total Hospitals (split by Government/Private)
      - Total Doctors
      - Active Prescriptions (system-wide)
    """

    # .count() runs a SQL COUNT(*) query - much faster than
    # loading every row into Python just to count them.
    total_patients = Patient.query.count()
    total_hospitals = Hospital.query.count()
    total_doctors = Doctor.query.count()

    # Count hospitals by type using filter_by()
    govt_hospitals = Hospital.query.filter_by(hospital_type="Government").count()
    private_hospitals = Hospital.query.filter_by(hospital_type="Private").count()

    # Count prescriptions where status == "Active"
    active_prescriptions = Prescription.query.filter_by(status="Active").count()

    return jsonify({
        "total_patients": total_patients,
        "total_hospitals": total_hospitals,
        "govt_hospitals": govt_hospitals,
        "private_hospitals": private_hospitals,
        "total_doctors": total_doctors,
        "active_prescriptions": active_prescriptions
    }), 200