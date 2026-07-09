import os  # read environment variables


class Config:

    SECRET_KEY = os.environ.get("SECRET_KEY", "medilink-dev-secret-key-change-this") # Flask to securely sign session cookies

    SQLALCHEMY_DATABASE_URI = "sqlite:///medilink.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False # setting change to memory save

    JSONIFY_PRETTYPRINT_REGULAR = True  #format JSON responses
    
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    PASSWORD_MIN_LENGTH = 8
    MFA_ISSUER = "MediLink Sri Lanka"

    SESSION_COOKIE_SECURE   = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ---------------------------------------------------------
    # OTP EMAIL SETTINGS
    # ---------------------------------------------------------

    # Gmail SMTP server settings (works for any Gmail account)
    MAIL_SERVER   = 'smtp.gmail.com'
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True   # TLS encrypts the email in transit
    MAIL_USE_SSL  = False

    # Replace with your Gmail address
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'medilinksrilanka@gmail.com')

    # Replace with the 16-character App Password from Step 1
    # Never hardcode this in production — use environment variable
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'tonj cnrp ccfq ilws')

    # This appears as the "From" name in the email
    MAIL_DEFAULT_SENDER = ('MediLink Sri Lanka', 'medilinksrilanka@gmail.com')

    # How many minutes before the OTP expires
    OTP_EXPIRY_MINUTES = 3