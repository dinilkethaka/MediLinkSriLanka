from functools import wraps #decorator
from flask import jsonify #return JSON responses
from flask_login import current_user

from models.user import User


def authenticate_user(username, password):
    user = User.query.filter_by(username=username).first()

    if user is None:
        return None

    if not user.check_password(password):
        return None

    return user


def role_required(*allowed_roles):

    def decorator(view_function):
        @wraps(view_function) 
        def wrapped_function(*args, **kwargs):

            if current_user.role not in allowed_roles:
                return jsonify({
                    "error": "Forbidden: you do not have permission to access this resource"
                }), 403

            return view_function(*args, **kwargs)

        return wrapped_function

    return decorator