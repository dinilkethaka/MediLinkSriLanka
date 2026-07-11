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

   #OTP settings

    # Gmail SMTP server settings
    MAIL_SERVER   = 'smtp.gmail.com'
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True  
    MAIL_USE_SSL  = False

    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'medilinksrilanka@gmail.com')

    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'tonj cnrp ccfq ilws')

    MAIL_DEFAULT_SENDER = ('MediLink Sri Lanka', 'medilinksrilanka@gmail.com')

    OTP_EXPIRY_MINUTES = 3