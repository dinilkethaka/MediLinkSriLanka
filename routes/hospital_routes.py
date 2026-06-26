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

# Add new patient
@hospital_bp.route("/api/hospital/patients", methods=["POST"])
@login_required
@role_required("hospital")
def register_patient():
    
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

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

    existing_patient = Patient.query.filter_by(nic=nic).first()
    if existing_patient:
        return jsonify({
            "error": "A patient with this NIC is already registered",
            "existing_patient_id": existing_patient.id
        }), 409  

    # convert the string using Python datetime module
    dob_string = data.get("date_of_birth")
    date_of_birth = None
    if dob_string:
        from datetime import datetime
        try:
            date_of_birth = datetime.strptime(dob_string, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "date_of_birth must be in YYYY-MM-DD format"}), 400

    gender = data.get("gender")
    if gender and gender not in ("Male", "Female"):
        return jsonify({"error": "gender must be 'Male', 'Female'"}), 400

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

# List patients
@hospital_bp.route("/api/hospital/patients", methods=["GET"])
@login_required
@role_required("hospital")
def list_hospital_patients():
    query = Patient.query.filter_by(hospital_id=current_user.hospital_id)

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

    blood_group = request.args.get("blood_group", "").strip()
    if blood_group:
        query = query.filter_by(blood_group=blood_group)

    patients = query.all()

    return jsonify({
        "patients": [p.to_dict() for p in patients]
    }), 200

# Get one patient
@hospital_bp.route("/api/hospital/patients/<int:patient_id>", methods=["GET"])
@login_required
@role_required("hospital")
def get_hospital_patient(patient_id):

    patient = Patient.query.get(patient_id)

    if patient is None:
        return jsonify({"error": "Patient not found"}), 404

    if patient.hospital_id != current_user.hospital_id:
        return jsonify({"error": "Forbidden: this patient is not registered at your hospital"}), 403

    # response with patient info + related records.
    result = patient.to_dict()

    #combine tables
    result["prescriptions"] = [p.to_dict() for p in patient.prescriptions]
    result["surgeries"] = [s.to_dict() for s in patient.surgeries]

    return jsonify({"patient": result}), 200


# Search doctor
@hospital_bp.route("/api/hospital/doctors", methods=["GET"])
@login_required
@role_required("hospital")
def search_doctors():
 
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


# Dashboard
@hospital_bp.route("/api/hospital/dashboard", methods=["GET"])
@login_required
@role_required("hospital")
def hospital_dashboard():
    
    hospital_id = current_user.hospital_id

    my_patients_count = Patient.query.filter_by(hospital_id=hospital_id).count()
    doctors_count = Doctor.query.filter_by(hospital_id=hospital_id).count()

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