# database/db.py
# ---------------------------------------------------------
# This file creates the single shared SQLAlchemy object.
#
# WHY do we need this in its own file?
# Because our models (user.py, hospital.py, etc.) need to import "db"
# to define their table columns - but app.py also needs "db" to connect
# everything together. If we created "db" inside app.py, we'd get a
# "circular import" error when models try to import it back.
#
# So instead: db.py creates "db" with no dependencies, and both
# app.py AND every model file import "db" from here. No circular imports!
# ---------------------------------------------------------

from flask_sqlalchemy import SQLAlchemy

# Create the SQLAlchemy database object.
# At this point it is not yet connected to any Flask app -
# that connection happens later in app.py via db.init_app(app)
db = SQLAlchemy()