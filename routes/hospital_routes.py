# routes/hospital_routes.py
# ---------------------------------------------------------
# This file defines all routes for the HOSPITAL role:
#
#   Patients:
#     POST /api/hospital/patients          -> register a new patient
#     GET  /api/hospital/patients          -> list patients at THIS hospital
#     GET  /api/hospital/patients/<id>     -> view one patient's full details
#
#   Doctors:
#     GET  /api/hospital/doctors           -> search doctors (all hospitals)
#
#   Dashboard:
#     GET  /api/hospital/dashboard         -> stats for this hospital
#
# EVERY route here requires:
#   @login_required
#   @role_required("hospital")
#
# IMPORTANT CONCEPT: current_user.hospital_id
# Flask-Login gives us "current_user" - the User object for whoever
# is logged in. Because our User model has a hospital_id column
# (set when the admin created this hospital's login account),
# we can use current_user.hospital_id to filter data so each
# hospital only sees ITS OWN patients - not other hospitals' data.
# ---------------------------------------------------------

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from database.db import db
from services.authentication_service import role_required

from models.patient import Patient
from models.doctor import Doctor
from models.hospital import Hospital
from models.prescription import Prescription
from models.surgery import SurgeryHistory


hospital_bp = Blueprint("hospital", __name__)


# =====================================================
# PATIENTS
# =====================================================

@hospital_bp.route("/api/hospital/patients", methods=["POST"])
@login_required
@role_required("hospital")
def register_patient():
    """
    Registers a NEW patient at THIS hospital.

    Expects JSON body, matching the "Register New Patient" modal:
        {
            "nic": "892501234V",
            "first_name": "Kasun",
            "last_name": "Perera",
            "date_of_birth": "1989-03-12",   <- format: YYYY-MM-DD
            "gender": "Male",                 <- "Male" / "Female" / "Other"
            "address": "45, Galle Road, Colombo 03",
            "phone_number": "+94772345678",
            "blood_group": "O+",
            "allergies": "Penicillin, Sulfonamides",
            "existing_conditions": "Hypertension"
        }

    SECURITY REQUIREMENT: "Protection against duplicate patient
    registrations" - we check if a patient with this NIC already
    exists BEFORE creating a new row.
    """

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # --- VALIDATE REQUIRED FIELDS ---
    nic = data.get("nic", "").strip()
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()

    missing = []
    if not nic:
        missing.append("nic")
    if not first_name:
        missing.append("first_name")
    if not last_name:
        missing.append("last_name")

    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # --- DUPLICATE NIC CHECK ---
    # This is the core "no duplicate registrations" security requirement.
    existing_patient = Patient.query.filter_by(nic=nic).first()
    if existing_patient:
        return jsonify({
            "error": "A patient with this NIC is already registered",
            "existing_patient_id": existing_patient.id
        }), 409  # 409 Conflict

    # --- PARSE DATE OF BIRTH ---
    # The frontend sends a date as a string like "1989-03-12".
    # SQLAlchemy's db.Date column needs an actual Python date object,
    # so we convert the string using Python's datetime module.
    dob_string = data.get("date_of_birth")
    date_of_birth = None
    if dob_string:
        from datetime import datetime
        try:
            # strptime() parses a string into a datetime, then .date()
            # extracts just the date part (no time).
            date_of_birth = datetime.strptime(dob_string, "%Y-%m-%d").date()
        except ValueError:
            # If the string isn't in YYYY-MM-DD format, reject the request
            # with a helpful error instead of crashing.
            return jsonify({"error": "date_of_birth must be in YYYY-MM-DD format"}), 400

    # --- VALIDATE GENDER (matches our Enum in the Patient model) ---
    gender = data.get("gender")
    if gender and gender not in ("Male", "Female", "Other"):
        return jsonify({"error": "gender must be 'Male', 'Female', or 'Other'"}), 400

    # --- CREATE THE PATIENT ---
    # current_user.hospital_id automatically links this patient to
    # the hospital that the logged-in user belongs to.
    new_patient = Patient(
        nic=nic,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        gender=gender,
        address=data.get("address"),
        phone_number=data.get("phone_number"),
        blood_group=data.get("blood_group"),
        allergies=data.get("allergies", "None"),
        existing_conditions=data.get("existing_conditions", "None"),
        hospital_id=current_user.hospital_id
    )

    db.session.add(new_patient)
    db.session.commit()

    return jsonify({
        "message": "Patient registered successfully",
        "patient": new_patient.to_dict()
    }), 201


@hospital_bp.route("/api/hospital/patients", methods=["GET"])
@login_required
@role_required("hospital")
def list_hospital_patients():
    """
    Lists patients registered at THIS hospital ONLY.

    Supports optional filters via query string:
        ?search=kasun          -> search by name or NIC
        ?blood_group=O+         -> filter by blood type

    Example: GET /api/hospital/patients?search=perera&blood_group=O+
    """

    # Start with a query scoped to THIS hospital only.
    # This is the key line for data isolation between hospitals!
    query = Patient.query.filter_by(hospital_id=current_user.hospital_id)

    # Apply search filter if provided
    search = request.args.get("search", "").strip()
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Patient.first_name.ilike(search_pattern),
                Patient.last_name.ilike(search_pattern),
                Patient.nic.ilike(search_pattern)
            )
        )

    # Apply blood group filter if provided
    blood_group = request.args.get("blood_group", "").strip()
    if blood_group:
        query = query.filter_by(blood_group=blood_group)

    patients = query.all()

    return jsonify({
        "patients": [p.to_dict() for p in patients]
    }), 200


@hospital_bp.route("/api/hospital/patients/<int:patient_id>", methods=["GET"])
@login_required
@role_required("hospital")
def get_hospital_patient(patient_id):
    """
    Returns FULL details for one patient, including:
      - basic info
      - prescriptions (medications)
      - surgery history

    This matches the "Patient Medical Record" modal in the frontend,
    which has tabs for History, Medications, and Info.

    NOTE: Hospitals can view patients registered at THEIR hospital.
    (If you want hospitals to view ANY patient for emergency access,
    remove the hospital_id check below - but for now we follow the
    stricter rule: each hospital sees its own patients.)
    """

    patient = Patient.query.get(patient_id)

    if patient is None:
        return jsonify({"error": "Patient not found"}), 404

    # Make sure this patient belongs to the logged-in hospital.
    if patient.hospital_id != current_user.hospital_id:
        return jsonify({"error": "Forbidden: this patient is not registered at your hospital"}), 403

    # Build the response with patient info + related records.
    result = patient.to_dict()

    # patient.prescriptions and patient.surgeries are relationships
    # defined in Phase 1's models - SQLAlchemy automatically fetches
    # the related rows for us.
    result["prescriptions"] = [p.to_dict() for p in patient.prescriptions]
    result["surgeries"] = [s.to_dict() for s in patient.surgeries]

    return jsonify({"patient": result}), 200


# =====================================================
# DOCTORS (search across all hospitals)
# =====================================================

@hospital_bp.route("/api/hospital/doctors", methods=["GET"])
@login_required
@role_required("hospital")
def search_doctors():
    """
    Searches for doctors ACROSS ALL HOSPITALS (not just this one).

    This matches the "Find Doctors" page in the Hospital dashboard,
    which lets hospital staff find any SLMC-registered doctor.

    Supports optional filters:
        ?search=silva           -> search by name or license number
        ?specialization=Cardiology
    """

    query = Doctor.query

    search = request.args.get("search", "").strip()
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Doctor.doctor_name.ilike(search_pattern),
                Doctor.license_number.ilike(search_pattern)
            )
        )

    specialization = request.args.get("specialization", "").strip()
    if specialization:
        query = query.filter_by(specialization=specialization)

    doctors = query.all()

    return jsonify({
        "doctors": [d.to_dict() for d in doctors]
    }), 200


# =====================================================
# DASHBOARD STATS
# =====================================================

@hospital_bp.route("/api/hospital/dashboard", methods=["GET"])
@login_required
@role_required("hospital")
def hospital_dashboard():
    """
    Returns stats for THIS hospital's dashboard:
      - My Patients (count)
      - Active Prescriptions (across this hospital's patients)
      - Doctors on Record (doctors who work at this hospital)
    """

    hospital_id = current_user.hospital_id

    # Count patients registered at this hospital.
    my_patients_count = Patient.query.filter_by(hospital_id=hospital_id).count()

    # Count doctors who work at this hospital.
    doctors_count = Doctor.query.filter_by(hospital_id=hospital_id).count()

    # Count active prescriptions for patients at THIS hospital.
    # We need a JOIN here: Prescription -> Patient -> filter by hospital_id.
    #
    # join(Patient) tells SQLAlchemy: "combine the Prescription table
    # with the Patient table using their relationship", then we can
    # filter on Patient.hospital_id even though we're querying Prescription.
    active_prescriptions_count = (
        Prescription.query
        .join(Patient)
        .filter(Patient.hospital_id == hospital_id)
        .filter(Prescription.status == "Active")
        .count()
    )

    return jsonify({
        "my_patients": my_patients_count,
        "active_prescriptions": active_prescriptions_count,
        "doctors_on_record": doctors_count
    }), 200