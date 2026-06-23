from database.db import db #Imports the SQLAlchemy database object.
from werkzeug.security import generate_password_hash, check_password_hash

#methods for user authentication
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "hospital", "doctor", name="user_roles"), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), nullable=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospital.id"), nullable=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=True)

    def set_password(self, plain_password): #save password
        self.password_hash = generate_password_hash(plain_password) #convert into hashing

    def check_password(self, plain_password): #check password
        return check_password_hash(self.password_hash, plain_password)
    
#User object into a Python dictionary
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "full_name": self.full_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "hospital_id": self.hospital_id,
            "doctor_id": self.doctor_id,
        }
        
#printing an object
    def __repr__(self):
        return f"<User {self.username} ({self.role})>"