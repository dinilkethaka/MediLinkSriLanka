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

#current hospital select
@doctor_bp.route("/api/doctor/hospitals", methods=["GET"])
@login_required
@role_required("doctor")
def list_hospitals_for_doctor():
    hospitals = Hospital.query.all()

    return jsonify({
        "hospitals": [h.to_dict() for h in hospitals]
    }), 200


# search patients
@doctor_bp.route("/api/doctor/patients", methods=["GET"])
@login_required
@role_required("doctor")
def search_patients_for_doctor():
  
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
        patients = Patient.query.all()

    return jsonify({
        "patients": [p.to_dict() for p in patients]
    }), 200

# View one patient
@doctor_bp.route("/api/doctor/patients/<int:patient_id>", methods=["GET"])
@login_required
@role_required("doctor")
def get_patient_for_doctor(patient_id):
    patient = Patient.query.get(patient_id)

    if patient is None:
        return jsonify({"error": "Patient not found"}), 404

    result = patient.to_dict()

    result["prescriptions"] = [p.to_dict() for p in patient.prescriptions]
    result["surgeries"] = [s.to_dict() for s in patient.surgeries]

    return jsonify({"patient": result}), 200


# Add prescription
@doctor_bp.route("/api/doctor/prescriptions", methods=["POST"])
@login_required
@role_required("doctor")
def add_prescription():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    patient_id = data.get("patient_id")
    medicine_name = data.get("medicine_name", "").strip() if data.get("medicine_name") else ""

    missing = []
    if not patient_id:
        missing.append("patient_id")
    if not medicine_name:
        missing.append("medicine_name")

    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    patient = Patient.query.get(patient_id)
    if patient is None:
        return jsonify({"error": f"No patient found with id {patient_id}"}), 404

    if current_user.doctor_id is None:
        return jsonify({"error": "This account is not linked to a doctor profile"}), 400

    doctor_id = current_user.doctor_id

    hospital_id = data.get("hospital_id")
    if hospital_id is not None:
        hospital = Hospital.query.get(hospital_id)
        if hospital is None:
            return jsonify({"error": f"No hospital found with id {hospital_id}"}), 404

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
        status="Active" 
    )

    db.session.add(new_prescription)
    db.session.commit()

    return jsonify({
        "message": "Prescription added successfully",
        "prescription": new_prescription.to_dict()
    }), 201

# Doctor's prescriptions
@doctor_bp.route("/api/doctor/prescriptions", methods=["GET"])
@login_required
@role_required("doctor")
def list_my_prescriptions():
    if current_user.doctor_id is None:
        return jsonify({"error": "This account is not linked to a doctor profile"}), 400

    prescriptions = Prescription.query.filter_by(doctor_id=current_user.doctor_id).all()

    return jsonify({
        "prescriptions": [p.to_dict() for p in prescriptions]
    }), 200