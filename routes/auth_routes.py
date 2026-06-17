# routes/auth_routes.py
# ---------------------------------------------------------
# This file defines all routes related to AUTHENTICATION:
#   POST /api/auth/login   -> log a user in
#   POST /api/auth/logout  -> log the current user out
#   GET  /api/auth/me      -> return info about the currently logged-in user
#
# We use a Flask "Blueprint" to group these routes together.
# A Blueprint is like a mini Flask app that we plug into the main app
# in app.py using app.register_blueprint(auth_bp).
# ---------------------------------------------------------

from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from services.authentication_service import authenticate_user

# Create the blueprint.
# "auth" = internal name Flask uses to identify this blueprint.
# __name__ = tells Flask which module this blueprint belongs to.
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """
    LOGIN endpoint.

    Expects a JSON body like:
        {
            "username": "admin1",
            "password": "mypassword123"
        }

    On success:
        - Creates a logged-in session for this user (via Flask-Login)
        - Returns 200 OK with the user's info (no password!)

    On failure:
        - Returns 401 Unauthorized with an error message
    """

    # request.get_json() reads the JSON body sent by the frontend.
    # We use silent=True so that if the body isn't valid JSON,
    # we get None instead of Flask crashing with an error page.
    data = request.get_json(silent=True)

    # If no JSON body was sent at all, that's a bad request.
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # .get() safely reads a key - if it's missing, we get None
    # instead of a KeyError crash.
    username = data.get("username")
    password = data.get("password")

    # Basic input validation: both fields are required.
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Call our service function (Phase 2's authentication_service.py)
    # to check if this username/password combo is valid.
    user = authenticate_user(username, password)

    # If authenticate_user() returned None, login failed.
    if user is None:
        return jsonify({"error": "Invalid username or password"}), 401

    # login_user() is provided by Flask-Login. It stores the user's ID
    # in the session (a secure cookie), so future requests from this
    # browser will be recognized as "logged in as this user".
    login_user(user)

    # Return the logged-in user's public info (using to_dict() from
    # the User model - this never includes the password hash).
    return jsonify({
        "message": "Login successful",
        "user": user.to_dict()
    }), 200


@auth_bp.route("/api/auth/logout", methods=["POST"])
@login_required  # this decorator blocks the request if nobody is logged in
def logout():
    """
    LOGOUT endpoint.

    Removes the current user's session, effectively logging them out.
    Requires the user to be logged in (via @login_required) - it
    wouldn't make sense to "log out" someone who isn't logged in.
    """
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/api/auth/me", methods=["GET"])
@login_required
def me():
    """
    "WHO AM I" endpoint.

    The frontend can call this when the page loads to check:
      - Is there a valid session? (if not, @login_required returns 401)
      - If yes, who is logged in and what is their role?

    This is useful for the frontend to decide which dashboard
    (Admin / Hospital / Doctor) to show after a page refresh.
    """
    # current_user is provided by Flask-Login. It automatically
    # refers to the User object for whoever is logged in during
    # this request (Flask-Login loads it using our user_loader,
    # which we'll define in app.py).
    return jsonify({"user": current_user.to_dict()}), 200