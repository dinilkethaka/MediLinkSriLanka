from flask import Blueprint, request, jsonify
from flask_login import login_required

from database.db import db
from services.authentication_service import role_required
from services.csv_import_service import import_patients_from_csv 

from models.hospital import Hospital
from models.doctor import Doctor
from models.patient import Patient
from models.prescription import Prescription
from models.user import User
from services.backup_service import run_backup

# Create the blueprint for all admin routes
admin_bp = Blueprint("admin", __name__)


# List hospitals
@admin_bp.route("/api/admin/hospitals", methods=["GET"])
@login_required
@role_required("admin")
def list_hospitals():
    hospitals = Hospital.query.all()
    return jsonify({
        "hospitals": [h.to_dict() for h in hospitals] #Hospitals bacame dictionary
    }), 200


#Add hospital
@admin_bp.route("/api/admin/hospitals", methods=["POST"])
@login_required
@role_required("admin")
def add_hospital():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400


    hospital_name = data.get("hospital_name")
    hospital_type = data.get("hospital_type")

    if not hospital_name:
        return jsonify({"error": "hospital_name is required"}), 400

    if hospital_type not in ("Government", "Private"):
        return jsonify({"error": "hospital_type must be 'Government' or 'Private'"}), 400

    existing = Hospital.query.filter_by(hospital_name=hospital_name).first()
    if existing:
        return jsonify({"error": "A hospital with this name already exists"}), 409

    new_hospital = Hospital(
        hospital_name=hospital_name,
        hospital_type=hospital_type,
        province=data.get("province"),
        city=data.get("city"),
        address=data.get("address"),
        bed_capacity=data.get("bed_capacity", 0),  # default
        contact_number=data.get("contact_number"),
        email=data.get("email")
    )

    # new row for insertion.
    db.session.add(new_hospital)
    db.session.commit()

    return jsonify({
        "message": "Hospital registered successfully",
        "hospital": new_hospital.to_dict()
    }), 201

#search hospital
@admin_bp.route("/api/admin/hospitals/<int:hospital_id>", methods=["GET"])
@login_required
@role_required("admin")
def get_hospital(hospital_id):
    hospital = Hospital.query.get(hospital_id)

    if hospital is None:
        return jsonify({"error": "Hospital not found"}), 404

    return jsonify({"hospital": hospital.to_dict()}), 200


# List doctors
@admin_bp.route("/api/admin/doctors", methods=["GET"])
@login_required
@role_required("admin")
def list_doctors():
    doctors = Doctor.query.all()
    return jsonify({
        "doctors": [d.to_dict() for d in doctors]
    }), 200

# Add doctor
@admin_bp.route("/api/admin/doctors", methods=["POST"])
@login_required
@role_required("admin")
def add_doctor():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    
    doctor_name = data.get("doctor_name")
    license_number = data.get("license_number")
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")

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


    if Doctor.query.filter_by(license_number=license_number).first():
        return jsonify({"error": "A doctor with this license number already exists"}), 409

    if Doctor.query.filter_by(email=email).first():
        return jsonify({"error": "A doctor with this email already exists"}), 409

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "This username is already taken"}), 409

   
    hospital_id = data.get("hospital_id")
    if hospital_id is not None:
        hospital = Hospital.query.get(hospital_id)
        if hospital is None:
            return jsonify({"error": f"No hospital found with id {hospital_id}"}), 404

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
    db.session.flush() #temporily insert

    # Create a account for new doctor
    new_user = User(
        username=username,
        role="doctor",
        full_name=doctor_name,
        email=email,
        phone_number=data.get("phone_number"),
        doctor_id=new_doctor.id
    )
    new_user.set_password(password)  # hash the password 
    db.session.add(new_user)


    db.session.commit()

    return jsonify({
        "message": "Doctor registered successfully",
        "doctor": new_doctor.to_dict()
    }), 201

# search doctor
@admin_bp.route("/api/admin/doctors/<int:doctor_id>", methods=["GET"])
@login_required
@role_required("admin")
def get_doctor(doctor_id):
    """Returns details for ONE specific doctor, by ID."""
    doctor = Doctor.query.get(doctor_id)

    if doctor is None:
        return jsonify({"error": "Doctor not found"}), 404

    return jsonify({"doctor": doctor.to_dict()}), 200


#patients search
@admin_bp.route("/api/admin/patients", methods=["GET"])
@login_required
@role_required("admin")
def list_all_patients():
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

# search by ID
@admin_bp.route("/api/admin/patients/<int:patient_id>", methods=["GET"])
@login_required
@role_required("admin")
def get_patient(patient_id):
    patient = Patient.query.get(patient_id)

    if patient is None:
        return jsonify({"error": "Patient not found"}), 404

    return jsonify({"patient": patient.to_dict()}), 200

#CSV inport
@admin_bp.route("/api/admin/patients/import-csv", methods=["POST"])
@login_required
@role_required("admin")
def import_patients_csv():

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Expected a form field named 'file'."}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only .csv files are supported"}), 400

    hospital_id_raw = request.form.get("hospital_id")

    hospital_id = None
    if hospital_id_raw:
        try:
            hospital_id = int(hospital_id_raw)
        except ValueError:
            return jsonify({"error": "hospital_id must be a number"}), 400

        hospital = Hospital.query.get(hospital_id)
        if hospital is None:
            return jsonify({"error": f"No hospital found with id {hospital_id}"}), 404

    # extract data from csv
    summary = import_patients_from_csv(file, hospital_id)

    return jsonify({
        "message": "CSV import completed",
        "summary": summary
    }), 200


# Dashboard
@admin_bp.route("/api/admin/dashboard", methods=["GET"])
@login_required
@role_required("admin")
def admin_dashboard():

    total_patients = Patient.query.count()
    total_hospitals = Hospital.query.count()
    total_doctors = Doctor.query.count()

    govt_hospitals = Hospital.query.filter_by(hospital_type="Government").count()
    private_hospitals = Hospital.query.filter_by(hospital_type="Private").count()

    active_prescriptions = Prescription.query.filter_by(status="Active").count()

    return jsonify({
        "total_patients": total_patients,
        "total_hospitals": total_hospitals,
        "govt_hospitals": govt_hospitals,
        "private_hospitals": private_hospitals,
        "total_doctors": total_doctors,
        "active_prescriptions": active_prescriptions
    }), 200
    

# =====================================================
# GOOGLE DRIVE BACKUP
# =====================================================

@admin_bp.route("/api/admin/backup", methods=["POST"])
@login_required
@role_required("admin")
def backup_to_drive():
    """
    Manual backup — triggered by the admin clicking
    "Backup Now" on the dashboard.
    """
    result = run_backup()

    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 500


@admin_bp.route("/api/admin/backup/list", methods=["GET"])
@login_required
@role_required("admin")
def list_backups():
    """
    Returns a list of all previous backups stored in Google Drive,
    newest first. Shown as a table on the Admin dashboard.
    """
    from services.backup_service import authenticate, get_or_create_folder

    service = authenticate()
    if not service:
        return jsonify({"error": "Google Drive not connected"}), 500

    try:
        folder_id = get_or_create_folder(service)

        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            orderBy="createdTime desc",
            fields="files(id, name, size, createdTime)",
            pageSize=20
        ).execute()

        backups = results.get('files', [])

        return jsonify({
            "backups": [
                {
                    "filename": f["name"],
                    "size_kb": round(int(f.get("size", 0)) / 1024, 1),
                    "created": f.get("createdTime", "")[:19].replace("T", " ")
                }
                for f in backups
            ]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500