# services/csv_import_service.py
# ---------------------------------------------------------
# This file contains the LOGIC for importing patients from a CSV file.
#
# WHAT THIS FILE DOES:
#   1. Reads the uploaded CSV file
#   2. Goes through each row
#   3. Validates the row has the minimum required fields (nic, first_name, last_name)
#   4. Skips rows where the NIC already exists in the database (duplicate protection)
#   5. Creates new Patient rows for everything else
#   6. Returns a SUMMARY of what happened (how many imported, how many skipped, and why)
#
# WHY return a detailed summary instead of just "success: true"?
# The frontend shows the admin EXACTLY what happened - e.g.
# "42 imported, 3 skipped (duplicate NIC), 1 skipped (missing NIC)".
# This is much more useful for real-world data cleanup.
# ---------------------------------------------------------

import csv          # Python's built-in CSV reading/writing module
import io           # lets us treat uploaded file data as a text stream
from datetime import datetime

from database.db import db
from models.patient import Patient


def import_patients_from_csv(file, hospital_id):
    """
    Imports patients from an uploaded CSV file.

    Parameters:
        file: a Werkzeug FileStorage object (from request.files['file'])
        hospital_id (int or None): which hospital these imported patients
                                     should be linked to (can be None if
                                     the CSV itself specifies it - but for
                                     simplicity, we assign ALL imported
                                     patients to ONE hospital chosen by
                                     the admin doing the import).

    Returns:
        A dictionary summary, e.g.:
        {
            "total_rows": 45,
            "imported": 42,
            "skipped_duplicate": 2,
            "skipped_invalid": 1,
            "errors": [
                {"row": 5, "reason": "Duplicate NIC: 892501234V"},
                {"row": 12, "reason": "Duplicate NIC: 961203456V"},
                {"row": 30, "reason": "Missing required field: last_name"}
            ]
        }
    """

    # --- STEP 1: Read the file content as TEXT ---
    # file.stream is the raw uploaded file data (bytes).
    # We decode it as UTF-8 text, then wrap it in io.StringIO so
    # Python's csv module can read it line-by-line like a normal file.
    #
    # "utf-8-sig" handles a common quirk: Excel sometimes adds an
    # invisible "BOM" (Byte Order Mark) at the start of CSV files,
    # which would otherwise mess up our first column name.
    raw_bytes = file.read()
    text_stream = io.StringIO(raw_bytes.decode("utf-8-sig"))

    # --- STEP 2: Set up the CSV reader ---
    # csv.DictReader reads each row as a DICTIONARY, using the
    # first row (header) as the keys.
    # Example: {"nic": "892501234V", "first_name": "Kasun", ...}
    reader = csv.DictReader(text_stream)

    # --- STEP 3: Prepare counters and result lists ---
    total_rows = 0
    imported_count = 0
    skipped_duplicate_count = 0
    skipped_invalid_count = 0
    errors = []  # list of {"row": <row number>, "reason": "..."}

    # --- STEP 4: Loop through each row ---
    # enumerate(reader, start=2) gives us a row number starting at 2,
    # because row 1 is the header row (so the first DATA row is "row 2"
    # - this matches what a person would see if they opened the CSV
    # in Excel, making error messages easier to understand).
    for row_number, row in enumerate(reader, start=2):
        total_rows += 1

        # .strip() removes extra whitespace/newlines around each value.
        # We use .get(key, "") so missing columns don't crash - they
        # just become empty strings.
        nic = (row.get("nic") or "").strip()
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()

        # --- VALIDATION: required fields ---
        if not nic:
            skipped_invalid_count += 1
            errors.append({"row": row_number, "reason": "Missing required field: nic"})
            continue  # "continue" skips to the next row in the loop

        if not first_name:
            skipped_invalid_count += 1
            errors.append({"row": row_number, "reason": "Missing required field: first_name"})
            continue

        if not last_name:
            skipped_invalid_count += 1
            errors.append({"row": row_number, "reason": "Missing required field: last_name"})
            continue

        # --- DUPLICATE CHECK ---
        # This is the "Duplicates (same NIC) are skipped" requirement
        # from the frontend's info box.
        existing = Patient.query.filter_by(nic=nic).first()
        if existing:
            skipped_duplicate_count += 1
            errors.append({"row": row_number, "reason": f"Duplicate NIC: {nic}"})
            continue

        # --- PARSE DATE OF BIRTH (optional field) ---
        dob_string = (row.get("date_of_birth") or "").strip()
        date_of_birth = None
        if dob_string:
            try:
                date_of_birth = datetime.strptime(dob_string, "%Y-%m-%d").date()
            except ValueError:
                # If the date is in a bad format, we don't fail the
                # whole row - we just leave date_of_birth empty and
                # note it in the errors list for the admin to review.
                errors.append({
                    "row": row_number,
                    "reason": f"Invalid date_of_birth '{dob_string}' (expected YYYY-MM-DD) - imported with blank DOB"
                })

        # --- VALIDATE GENDER (optional field) ---
        gender = (row.get("gender") or "").strip()
        if gender not in ("Male", "Female", "Other"):
            # If gender is missing or not one of our 3 allowed values,
            # we just leave it blank rather than rejecting the row.
            gender = None

        # --- CREATE THE PATIENT ROW ---
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

    # --- STEP 5: Save everything to the database at once ---
    # We commit ONCE after the loop (not inside the loop) for
    # better performance - one database transaction instead of
    # hundreds of tiny ones.
    db.session.commit()

    # --- STEP 6: Return the summary ---
    return {
        "total_rows": total_rows,
        "imported": imported_count,
        "skipped_duplicate": skipped_duplicate_count,
        "skipped_invalid": skipped_invalid_count,
        "errors": errors
    }