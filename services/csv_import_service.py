import csv         
import io           # uploaded file data as a text stream
from datetime import datetime

from database.db import db
from models.patient import Patient


def import_patients_from_csv(file, hospital_id):

    raw_bytes = file.read()
    text_stream = io.StringIO(raw_bytes.decode("utf-8-sig"))

    reader = csv.DictReader(text_stream)


    total_rows = 0
    imported_count = 0
    skipped_duplicate_count = 0
    skipped_invalid_count = 0
    errors = []  # list of errors

    for row_number, row in enumerate(reader, start=2):
        total_rows += 1

        # .strip() removes extra whitespace/newlines 
        nic = (row.get("nic") or "").strip()
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()

        if not nic:
            skipped_invalid_count += 1
            errors.append({"row": row_number, "reason": "Missing required field: nic"})
            continue  

        if not first_name:
            skipped_invalid_count += 1
            errors.append({"row": row_number, "reason": "Missing required field: first_name"})
            continue

        if not last_name:
            skipped_invalid_count += 1
            errors.append({"row": row_number, "reason": "Missing required field: last_name"})
            continue

        existing = Patient.query.filter_by(nic=nic).first()
        if existing:
            skipped_duplicate_count += 1
            errors.append({"row": row_number, "reason": f"Duplicate NIC: {nic}"})
            continue

        dob_string = (row.get("date_of_birth") or "").strip()
        date_of_birth = None
        if dob_string:
            try:
                date_of_birth = datetime.strptime(dob_string, "%Y-%m-%d").date()
            except ValueError:
                errors.append({
                    "row": row_number,
                    "reason": f"Invalid date_of_birth '{dob_string}' (expected YYYY-MM-DD) - imported with blank DOB"
                })

        gender = (row.get("gender") or "").strip()
        if gender not in ("Male", "Female"):
            gender = None

        new_patient = Patient(
            nic=nic,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender,
            address=(row.get("address") or "").strip() or None,
            phone_number=(row.get("phone_number") or "").strip() or None,
            blood_group=(row.get("blood_group") or "").strip() or None,
            allergies=(row.get("allergies") or "").strip() or "None",
            existing_conditions=(row.get("existing_conditions") or "").strip() or "None",
            hospital_id=hospital_id
        )

        db.session.add(new_patient)
        imported_count += 1

    db.session.commit()

    return {
        "total_rows": total_rows,
        "imported": imported_count,
        "skipped_duplicate": skipped_duplicate_count,
        "skipped_invalid": skipped_invalid_count,
        "errors": errors
    }