from flask import Blueprint, request, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user

from extensions import mail
from services.authentication_service import authenticate_user
from services.otp_service import (
    generate_otp,
    store_otp,
    send_otp_email,
    verify_otp
)
from models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # verify credentials
    user = authenticate_user(username, password)
    if user is None:
        return jsonify({"error": "Invalid username or password"}), 401

    if user.role == "admin":
        login_user(user)
        return jsonify({
            "otp_sent": False,
            "message": "Login successful",
            "user": user.to_dict()
        }), 200

    if not user.email:
        return jsonify({
            "error": "No email address on file for this account. Contact admin."
        }), 400

    otp_code = generate_otp()
    store_otp(user.id, otp_code)

    sent = send_otp_email(mail, user.email, user.full_name, otp_code)

    if not sent:
        return jsonify({
            "error": "Failed to send OTP email. Check email configuration in config.py."
        }), 500

    return jsonify({
        "otp_sent": True,
        "message": "Verification code sent to your email.",
    }), 200


@auth_bp.route("/api/auth/verify-otp", methods=["POST"])
def verify_otp_route():

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    entered_otp = data.get("otp", "").strip()
    if not entered_otp:
        return jsonify({"error": "OTP code is required"}), 400

    pending_user_id = session.get('otp_user_id')
    if not pending_user_id:
        return jsonify({"error": "No login in progress. Please start from Step 1."}), 400

    is_valid, error_msg = verify_otp(pending_user_id, entered_otp)
    if not is_valid:
        return jsonify({"error": error_msg}), 401

    user = User.query.get(pending_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 400

    login_user(user)

    return jsonify({
        "message": "Login successful",
        "user": user.to_dict()
    }), 200


@auth_bp.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/api/auth/me", methods=["GET"])
@login_required
def me():
    return jsonify({"user": current_user.to_dict()}), 200