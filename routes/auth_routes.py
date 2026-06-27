from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from services.authentication_service import authenticate_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = authenticate_user(username, password)

    if user is None:
        return jsonify({"error": "Invalid username or password"}), 401

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