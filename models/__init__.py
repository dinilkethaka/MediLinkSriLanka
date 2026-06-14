# models/__init__.py
# ---------------------------------------------------------
# This file marks "models" as a Python package.
#
# We also import every model class here. This means that when
# app.py does:  from models import User, Hospital, Doctor, ...
# it will work, AND it ensures SQLAlchemy "sees" every model
# class before we call db.create_all() (which creates the tables).
# ---------------------------------------------------------

from .user import User
from .hospital import Hospital
from .doctor import Doctor
from .patient import Patient
from .prescription import Prescription
from .surgery import SurgeryHistory