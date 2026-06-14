from database.db import db


class SurgeryHistory(db.Model):
    __tablename__ = "surgery_history"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospital.id"), nullable=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=True)

    surgery_name = db.Column(db.String(150), nullable=False)
    surgery_date = db.Column(db.Date, nullable=True)
    remarks = db.Column(db.Text, nullable=True)

    patient = db.relationship("Patient", back_populates="surgeries")
    doctor = db.relationship("Doctor", back_populates="surgeries")

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "hospital_id": self.hospital_id,
            "doctor_id": self.doctor_id,
            "surgery_name": self.surgery_name,
            "surgery_date": self.surgery_date.isoformat() if self.surgery_date else None,
            "remarks": self.remarks,
        }

    def __repr__(self):
        return f"<SurgeryHistory {self.surgery_name} for patient {self.patient_id}>"