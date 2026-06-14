from database.db import db


class Doctor(db.Model):
    __tablename__ = "doctor"

    id = db.Column(db.Integer, primary_key=True)
    doctor_name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=True)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), nullable=True)
    nic = db.Column(db.String(20), unique=True, nullable=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospital.id"), nullable=True)

    hospital = db.relationship("Hospital", back_populates="doctors")
    prescriptions = db.relationship("Prescription", back_populates="doctor")
    surgeries = db.relationship("SurgeryHistory", back_populates="doctor")

    def to_dict(self):
        return {
            "id": self.id,
            "doctor_name": self.doctor_name,
            "specialization": self.specialization,
            "license_number": self.license_number,
            "email": self.email,
            "phone_number": self.phone_number,
            "nic": self.nic,
            "hospital_id": self.hospital_id,
            "hospital_name": self.hospital.hospital_name if self.hospital else None,
        }

    def __repr__(self):
        return f"<Doctor {self.doctor_name} ({self.specialization})>"