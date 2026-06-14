from database.db import db


class Hospital(db.Model):
    __tablename__ = "hospital"

    id = db.Column(db.Integer, primary_key=True)
    hospital_name = db.Column(db.String(100), nullable=False)
    hospital_type = db.Column(db.Enum("Government", "Private", name="hospital_types"), nullable=False)
    province = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    bed_capacity = db.Column(db.Integer, default=0)
    contact_number = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)

    doctors = db.relationship("Doctor", back_populates="hospital")
    patients = db.relationship("Patient", back_populates="hospital")

    def to_dict(self):
        return {
            "id": self.id,
            "hospital_name": self.hospital_name,
            "hospital_type": self.hospital_type,
            "province": self.province,
            "city": self.city,
            "address": self.address,
            "bed_capacity": self.bed_capacity,
            "contact_number": self.contact_number,
            "email": self.email,
            "doctor_count": len(self.doctors),
        }

    def __repr__(self):
        return f"<Hospital {self.hospital_name} ({self.hospital_type})>"