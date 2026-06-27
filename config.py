import os  # read environment variables


class Config:

    SECRET_KEY = os.environ.get("SECRET_KEY", "medilink-dev-secret-key-change-this") # Flask to securely sign session cookies

    SQLALCHEMY_DATABASE_URI = "sqlite:///medilink.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False # setting change to memory save

    JSONIFY_PRETTYPRINT_REGULAR = True  #format JSON responses