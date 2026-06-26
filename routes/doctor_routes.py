# routes/doctor_routes.py
# ---------------------------------------------------------
# This file defines all routes for the DOCTOR role:
#
#   Hospitals:
#     GET  /api/doctor/hospitals             -> list all hospitals
#                                                (for the "select your
#                                                 current hospital" picker)
#
#   Patients:
#     GET  /api/doctor/patients              -> search patients (ALL hospitals)
#     GET  /api/doctor/patients/<id>         -> view one patient + full history
#
#   Prescriptions:
#     POST /api/doctor/prescriptions         -> add a new prescription
#     GET  /api/doctor/prescriptions         -> list prescriptions THIS doctor wrote
#
# EVERY route here requires:
#   @login_required
#   @role_required("doctor")
#
# IMPORTANT CONCEPT: current_user.doctor_id
# This links the logged-in User account to their Doctor profile row.
# We use it to record WHO wrote a prescription, and to filter
# "my prescriptions" lists.
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


doctor_bp = Blueprint("doctor", __name__)


# =====================================================
# HOSPITALS (for the "select your current hospital" picker)
# =====================================================

@doctor_bp.route("/api/doctor/hospitals", methods=["GET"])
@login_required
@role_required("doctor")
def list_hospitals_for_doctor():
    """
    Returns a list of ALL hospitals.

    This matches the "Select Your Current Hospital" modal that
    appears after a doctor logs in - they choose which hospital
    they're working at for this session.
    """
    hospitals = Hospital.query.all()

    return jsonify({
        "hospitals": [h.to_dict() for h in hospitals]
    }), 200


# =====================================================
# PATIENTS (search across ALL hospitals)
# =====================================================

@doctor_bp.route("/api/doctor/patients", methods=["GET"])
@login_required
@role_required("doctor")
def search_patients_for_doctor():
    """
    Searches for patients ACROSS ALL HOSPITALS.

    This matches the "Search Patients" page in the Doctor dashboard.
    Doctors need broad access to find any patient's record, since
    patients may visit different hospitals over time.

    Supports an optional search query string:
        GET /api/doctor/patients?search=kasun

    This searches by name OR NIC.
    """

    search = request.args.get("search", "").strip()

    if search:
        search_pattern = f"%{search}%"
        patients = Patient.query.filter(
            db.or_(
                Patient.first_name.ilike(search_pattern),
                Patient.last_name.ilike(search_pattern),
                Patient.nic.ilike(search_pattern)
            )
        ).all()
    else:
        # If no search term is given, we return ALL patients.
        # (In a real production system with thousands of patients,
        # we might require a search term or paginate - but for our
        # learning project, returning everyone is fine.)
        patients = Patient.query.all()

    return jsonify({
        "patients": [p.to_dict() for p in patients]
    }), 200


@doctor_bp.route("/api/doctor/patients/<int:patient_id>", methods=["GET"])
@login_required
@role_required("doctor")
def get_patient_for_doctor(patient_id):
    """
    Returns FULL details for one patient, including:
      - basic info (allergies, conditions, blood group, etc.)
      - prescriptions (medication history)
      - surgery history

    UNLIKE hospital_routes.py's get_hospital_patient(), there is
    NO hospital_id check here - doctors can view ANY patient,
    from any hospital. This matches the project's goal of a
    "centralized" record system.
    """

    patient = Patient.query.get(patient_id)

    if patient is None:
        return jsonify({"error": "Patient not found"}), 404

    result = patient.to_dict()

    # Include related records using the relationships defined
    # in Phase 1's models.
    result["prescriptions"] = [p.to_dict() for p in patient.prescriptions]
    result["surgeries"] = [s.to_dict() for s in patient.surgeries]

    return jsonify({"patient": result}), 200


# =====================================================
# PRESCRIPTIONS
# =====================================================

@doctor_bp.route("/api/doctor/prescriptions", methods=["POST"])
@login_required
@role_required("doctor")
def add_prescription():
    """
    Adds a new prescription for a patient.

    Expects JSON body, matching the "Add New Prescription" modal:
        {
            "patient_id": 1,
            "medicine_name": "Amlodipine",
            "dosage": "5mg",
            "frequency": "Once daily",
            "duration": "30 days",
            "route": "Oral",
            "notes": "Take after breakfast",
            "hospital_id": 1   <- the hospital the doctor is CURRENTLY
                                   working at (selected at login)
        }

    current_user.doctor_id tells us WHICH doctor is writing this
    prescription - we don't trust the frontend to send doctor_id,
    we use the logged-in user's own doctor profile. This prevents
    a doctor from writing prescriptions "as" another doctor.
    """

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # --- VALIDATE REQUIRED FIELDS ---
    patient_id = data.get("patient_id")
    medicine_name = data.get("medicine_name", "").strip() if data.get("medicine_name") else ""

    missing = []
    if not patient_id:
        missing.append("patient_id")
    if not medicine_name:
        missing.append("medicine_name")

    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # --- CHECK THE PATIENT EXISTS ---
    patient = Patient.query.get(patient_id)
    if patient is None:
        return jsonify({"error": f"No patient found with id {patient_id}"}), 404

    # --- CHECK THE LOGGED-IN USER HAS A LINKED DOCTOR PROFILE ---
    # current_user.doctor_id was set when the admin created this
    # doctor's account (see Phase 3's add_doctor route, or seed.py).
    if current_user.doctor_id is None:
        return jsonify({"error": "This account is not linked to a doctor profile"}), 400

    doctor_id = current_user.doctor_id

    # --- OPTIONAL: validate hospital_id if provided ---
    hospital_id = data.get("hospital_id")
    if hospital_id is not None:
        hospital = Hospital.query.get(hospital_id)
        if hospital is None:
            return jsonify({"error": f"No hospital found with id {hospital_id}"}), 404

    # --- CREATE THE PRESCRIPTION ---
    new_prescription = Prescription(
        patient_id=patient_id,
        doctor_id=doctor_id,
        hospital_id=hospital_id,
        medicine_name=medicine_name,
        dosage=data.get("dosage"),
        frequency=data.get("frequency"),
        duration=data.get("duration"),
        route=data.get("route"),
        notes=data.get("notes"),
        status="Active"  # new prescriptions always start as "Active"
    )

    db.session.add(new_prescription)
    db.session.commit()

    return jsonify({
        "message": "Prescription added successfully",
        "prescription": new_prescription.to_dict()
    }), 201


@doctor_bp.route("/api/doctor/prescriptions", methods=["GET"])
@login_required
@role_required("doctor")
def list_my_prescriptions():
    """
    Lists all prescriptions written by the LOGGED-IN doctor.

    This matches the "Prescriptions I've Issued" page in the
    Doctor dashboard.
    """

    if current_user.doctor_id is None:
        return jsonify({"error": "This account is not linked to a doctor profile"}), 400

    # filter_by(doctor_id=...) -> WHERE doctor_id = current_user.doctor_id
    prescriptions = Prescription.query.filter_by(doctor_id=current_user.doctor_id).all()

    return jsonify({
        "prescriptions": [p.to_dict() for p in prescriptions]
    }), 200