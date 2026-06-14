from database.db import db


class Patient(db.Model):
    __tablename__ = "patient"

    id = db.Column(db.Integer, primary_key=True)
    nic = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.Enum("Male", "Female", "Other", name="patient_genders"), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    allergies = db.Column(db.String(255), nullable=True)
    existing_conditions = db.Column(db.String(255), nullable=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospital.id"), nullable=True)

    hospital = db.relationship("Hospital", back_populates="patients")
    prescriptions = db.relationship("Prescription", back_populates="patient", cascade="all, delete-orphan")
    surgeries = db.relationship("SurgeryHistory", back_populates="patient", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {
            "id": self.id,
            "nic": self.nic,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "address": self.address,
            "phone_number": self.phone_number,
            "blood_group": self.blood_group,
            "allergies": self.allergies,
            "existing_conditions": self.existing_conditions,
            "hospital_id": self.hospital_id,
            "hospital_name": self.hospital.hospital_name if self.hospital else None,
        }

    def __repr__(self):
        return f"<Patient {self.full_name} ({self.nic})>"