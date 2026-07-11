import random
import string
from datetime import datetime, timedelta
from flask import session, current_app
from flask_mail import Message


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def store_otp(user_id, otp_code):
    expiry_minutes = current_app.config.get('OTP_EXPIRY_MINUTES', 3)
    expiry_time = datetime.utcnow() + timedelta(minutes=expiry_minutes)


    session['otp_user_id'] = user_id
    session['otp_code']    = otp_code
    session['otp_expiry']  = expiry_time.isoformat()


def send_otp_email(mail, user_email, user_name, otp_code):
    expiry_minutes = current_app.config.get('OTP_EXPIRY_MINUTES', 3)

    try:
        msg = Message(
            subject="MediLink Login Verification Code",
            recipients=[user_email]
        )

        # Plain text fallback
        msg.body = (
            f"Hello {user_name},\n\n"
            f"Your MediLink login verification code is:\n\n"
            f"{otp_code}\n\n"
            f"This code expires in {expiry_minutes} minutes.\n\n"
            f"If you did not attempt to log in, please ignore this email.\n\n"
            f"MediLink Sri Lanka"
        )

        # HTML version
        msg.html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:24px">
  <div style="text-align:center;margin-bottom:24px">
    <h2 style="color:#1e3a5f;margin:0">MediLink Sri Lanka</h2>
    <p style="color:#5c7fa8;margin:4px 0 0">Centralized Health Management System</p>
  </div>

  <div style="background:#f4f7fb;border-radius:8px;padding:24px;text-align:center">
    <p style="color:#1e3a5f;margin:0 0 8px">Hello <strong>{user_name}</strong>,</p>
    <p style="color:#5c7fa8;margin:0 0 20px;font-size:14px">
      Your login verification code is:
    </p>

    <div style="background:#fff;border:1px solid #dce6f5;border-radius:6px;
                padding:16px 32px;display:inline-block;margin-bottom:20px">
      <span style="font-size:36px;font-weight:700;letter-spacing:10px;color:#2563eb">
        {otp_code}
      </span>
    </div>

    <p style="color:#5c7fa8;font-size:13px;margin:0">
      This code expires in <strong>{expiry_minutes} minutes</strong>.
    </p>
  </div>

  <p style="color:#8baece;font-size:12px;text-align:center;margin-top:20px">
    If you did not attempt to log in to MediLink, please ignore this email.
  </p>
</body>
</html>
"""
        mail.send(msg)
        return True

    except Exception as e:
        print(f"Failed to send OTP email to {user_email}: {e}")
        return False


def verify_otp(user_id, entered_code):
    stored_user_id = session.get('otp_user_id')
    stored_code    = session.get('otp_code')
    stored_expiry  = session.get('otp_expiry')

    if not stored_code or not stored_expiry or not stored_user_id:
        return False, "No OTP found. Please log in again."

    if stored_user_id != user_id:
        return False, "OTP mismatch. Please log in again."

    if datetime.utcnow() > datetime.fromisoformat(stored_expiry):
        _clear_otp_session()
        return False, "OTP has expired. Please log in again."

    if entered_code.strip() != stored_code:
        return False, "Invalid OTP code. Please try again."

    _clear_otp_session()
    return True, None


def _clear_otp_session():
    """Removes OTP data from the session."""
    session.pop('otp_user_id', None)
    session.pop('otp_code',    None)
    session.pop('otp_expiry',  None)