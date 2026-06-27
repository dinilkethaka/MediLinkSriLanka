from app import create_app
from database.db import db
from models.user import User
from models.hospital import Hospital
from models.doctor import Doctor


def run_seed():
    app = create_app()

    with app.app_context():

        # Create Admin
        
        admin = User.query.filter_by(username="admin1").first()
        if admin is None:
            admin = User(
                username="admin1",
                role="admin",
                full_name="System Administrator",
                email="admin@medilink.lk",
                phone_number="0112000000"
            )
            
            admin.set_password("Admin@123")
            db.session.add(admin)
            print(" Created admin user: username='admin1', password='Admin@123'")
        else:
            print(" Admin user already exists, skipping.")

        # Create hospital
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
            db.session.flush()
            print(f" Created hospital: {hospital.hospital_name} (id={hospital.id})")
        else:
            print(" Hospital already exists, skipping.")

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
            print(" Created hospital user: username='hospital1', password='Hospital@123'")
        else:
            print(" Hospital user already exists, skipping.")

        # Create doctor

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
            db.session.flush()  
            print(f" Created doctor: {doctor.doctor_name} (id={doctor.id})")
        else:
            print("Doctor already exists, skipping.")

        doctor_user = User.query.filter_by(username="doctor1").first()
        if doctor_user is None:
            doctor_user = User(
                username="doctor1",
                role="doctor",
                full_name="Dr. Ruwan Silva",
                email="doctor1@medilink.lk",
                phone_number="0771234567",
                doctor_id=doctor.id  
            )
            doctor_user.set_password("Doctor@123")
            db.session.add(doctor_user)
            print(" Created doctor user: username='doctor1', password='Doctor@123'")
        else:
            print(" Doctor user already exists, skipping.")

        db.session.commit()
        print("🎉 Seeding complete!")


if __name__ == "__main__":
    run_seed()