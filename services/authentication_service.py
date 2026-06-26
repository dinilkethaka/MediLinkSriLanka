# services/authentication_service.py
# ---------------------------------------------------------
# This file contains:
#   1. authenticate_user() - checks username/password
#   2. role_required()     - a decorator for Role-Based Access Control (RBAC)
# ---------------------------------------------------------

from functools import wraps
from flask import jsonify
from flask_login import current_user

from models.user import User


def authenticate_user(username, password):
    """
    Checks if a username + password combination is correct.
    Returns the User object if valid, otherwise None.
    (See full explanation in the comments from earlier in Phase 2.)
    """
    user = User.query.filter_by(username=username).first()

    if user is None:
        return None

    if not user.check_password(password):
        return None

    return user


def role_required(*allowed_roles):
    """
    This is a CUSTOM DECORATOR for Role-Based Access Control (RBAC).

    HOW TO USE IT:
        @app.route("/api/admin/something")
        @login_required          # <- must be logged in at all
        @role_required("admin")  # <- AND must have role "admin"
        def some_admin_only_route():
            ...

    You can allow multiple roles too:
        @role_required("admin", "hospital")

    HOW IT WORKS (for beginners):
    `role_required("admin")` is a function that RETURNS another function
    (called a "decorator"). That returned decorator wraps your route
    function, adding a permission check BEFORE your route's code runs.

    Step by step:
      1. role_required("admin") runs ONCE, when Flask is setting up routes.
         It "remembers" that allowed_roles = ("admin",).
      2. It returns `decorator`, which Flask uses to wrap your route function.
      3. Every time a request comes in, `wrapped_function` runs FIRST:
         - It checks current_user.role
         - If it's not in allowed_roles, it returns a 403 Forbidden response
           and your actual route code never runs.
         - If it IS allowed, it calls the real route function normally.
    """

    def decorator(view_function):
        @wraps(view_function)  # keeps the original function's name/docs intact
        def wrapped_function(*args, **kwargs):

            # current_user.role works because current_user is a User object
            # (Flask-Login already confirmed they're logged in, assuming
            # @login_required was used ABOVE this decorator).
            if current_user.role not in allowed_roles:
                return jsonify({
                    "error": "Forbidden: you do not have permission to access this resource"
                }), 403

            # Role is allowed - run the actual route function.
            return view_function(*args, **kwargs)

        return wrapped_function

    return decorator