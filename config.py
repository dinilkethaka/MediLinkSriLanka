# config.py
# ---------------------------------------------------------
# This file holds configuration settings for our Flask app.
# Keeping settings in one place makes it easy to change them
# later without hunting through the whole codebase.
# ---------------------------------------------------------

import os  # "os" lets us read environment variables (useful for secrets)


class Config:
    """
    The Config class groups together all our app's settings.
    Flask will read these values when we call app.config.from_object(Config).
    """

    # SECRET_KEY is used by Flask to securely sign session cookies.
    # In a real production app, NEVER hardcode this - load it from an
    # environment variable or .env file. For learning purposes, we provide
    # a default fallback value.
    SECRET_KEY = os.environ.get("SECRET_KEY", "medilink-dev-secret-key-change-this")

    # SQLALCHEMY_DATABASE_URI tells SQLAlchemy how to connect to our database.
    # Format for MySQL with PyMySQL driver:
    #   mysql+pymysql://<username>:<password>@<host>/<database_name>
    #
    # Example: if your MySQL username is "root", password is "password123",
    # and the database is "MediLink" (created in Firstdata.sql), it would be:
    #   mysql+pymysql://root:password123@localhost/MediLink
    #
    # For beginners who don't have MySQL set up yet, you can instead use
    # SQLite (a simple file-based database) by uncommenting the line below.

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost/MediLink"
)
    SQLALCHEMY_DATABASE_URI = "sqlite:///medilink.db"
    # Uncomment this line instead if you want to use SQLite for quick testing
    # (no MySQL installation required). SQLite stores everything in one file.
    # SQLALCHEMY_DATABASE_URI = "sqlite:///medilink.db"

    # This setting turns OFF a feature we don't need (event tracking),
    # which also removes a warning message and saves memory.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # This makes JSON responses from our API "pretty printed" (nicely
    # indented), which is easier to read while learning/debugging.
    JSONIFY_PRETTYPRINT_REGULAR = True