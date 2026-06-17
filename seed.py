# seed.py
# ---------------------------------------------------------
# This script INSERTS some starter data into our database so we
# have accounts to log in with. Run it ONCE with:
#
#     python seed.py
#
# WHY do we need this?
# db.create_all() (from Phase 1) only creates EMPTY tables.
# It does not create any actual login accounts. Without this
# script, there is nothing to log in as!
#
# SAFE TO RE-RUN? This script checks if data already exists
# before inserting, so running it twice won't create duplicates.
# ---------------------------------------------------------

from app import create_app
from database.db import db
from models.user import User
from models.hospital import Hospital
from models.doctor import Doctor


def run_seed():
    app = create_app()

    # We need an "app context" to talk to the database outside of
    # a normal web request (same idea as in app.py's create_app()).
    with app.app_context():

        # ---------------------------------------------------
        # 1. Create an Admin user (if one doesn't already exist)
        # ---------------------------------------------------
        admin = User.query.filter_by(username="admin1").first()
        if admin is None:
            admin = User(
                username="admin1",
                role="admin",
                full_name="System Administrator",
                email="admin@medilink.lk",
                phone_number="0112000000"
            )
            # set_password() hashes the password before storing it
            admin.set_password("Admin@123")
            db.session.add(admin)
            print("✅ Created admin user: username='admin1', password='Admin@123'")
        else:
            print("ℹ️ Admin user already exists, skipping.")

        # ---------------------------------------------------
        # 2. Create a Hospital + a Hospital-role login user
        # ---------------------------------------------------
        hospital = Hospital.query.filter_by(hospital_name="Colombo National Hospital").first()
        if hospital is None:
            hospital = Hospital(
                hospital_name="Colombo National Hospital",
                hospital_type="Government",
                province="Western Province",
                city="Colombo",
                address="Regent St, Colombo 8",
                bed_capacity=3000,
                contact_number="0112691111",
                email="admin@cnh.gov.lk"
            )
            db.session.add(hospital)
            # flush() sends this INSERT to the database immediately so
            # "hospital.id" gets filled in by the database (auto-increment),
            # WITHOUT fully "committing" yet. This lets us use hospital.id
            # below for the hospital_user's hospital_id field.
            db.session.flush()
            print(f"✅ Created hospital: {hospital.hospital_name} (id={hospital.id})")
        else:
            print("ℹ️ Hospital already exists, skipping.")

        hospital_user = User.query.filter_by(username="hospital1").first()
        if hospital_user is None:
            hospital_user = User(
                username="hospital1",
                role="hospital",
                full_name="Colombo National Hospital",
                email="hospital1@medilink.lk",
                phone_number="0112691111",
                hospital_id=hospital.id  # links this login to the hospital above
            )
            hospital_user.set_password("Hospital@123")
            db.session.add(hospital_user)
            print("✅ Created hospital user: username='hospital1', password='Hospital@123'")
        else:
            print("ℹ️ Hospital user already exists, skipping.")

        # ---------------------------------------------------
        # 3. Create a Doctor + a Doctor-role login user
        # ---------------------------------------------------
        doctor = Doctor.query.filter_by(license_number="SLMC-10021").first()
        if doctor is None:
            doctor = Doctor(
                doctor_name="Dr. Ruwan Silva",
                specialization="Cardiology",
                license_number="SLMC-10021",
                email="ruwan.silva@medilink.lk",
                phone_number="0771234567",
                nic="952501234V",
                hospital_id=hospital.id
            )
            db.session.add(doctor)
            db.session.flush()  # so doctor.id is available below
            print(f"✅ Created doctor: {doctor.doctor_name} (id={doctor.id})")
        else:
            print("ℹ️ Doctor already exists, skipping.")

        doctor_user = User.query.filter_by(username="doctor1").first()
        if doctor_user is None:
            doctor_user = User(
                username="doctor1",
                role="doctor",
                full_name="Dr. Ruwan Silva",
                email="doctor1@medilink.lk",
                phone_number="0771234567",
                doctor_id=doctor.id  # links this login to the doctor above
            )
            doctor_user.set_password("Doctor@123")
            db.session.add(doctor_user)
            print("✅ Created doctor user: username='doctor1', password='Doctor@123'")
        else:
            print("ℹ️ Doctor user already exists, skipping.")

        # ---------------------------------------------------
        # Finally, save everything to the database permanently.
        # ---------------------------------------------------
        db.session.commit()
        print("🎉 Seeding complete!")


if __name__ == "__main__":
    run_seed()