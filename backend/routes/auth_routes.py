"""Authentication routes - Register, Login, OTP, Profile."""
from datetime import datetime
from functools import wraps

from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    get_jwt_identity, jwt_required, verify_jwt_in_request
)

from models.activity_model import ActivityLogModel
from models.user_model import UserModel
from utils.database import serialize_doc
from utils.response import error_response, success_response
from utils.security import generate_otp, hash_password, otp_expiry, verify_password
from utils.validators import sanitize_input, validate_email, validate_password

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def admin_required(fn):
    """Decorator for admin-only routes."""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = UserModel.find_by_id(user_id)
        if not user or user.get("role") != "admin":
            return error_response("Admin access required", 403)
        return fn(*args, **kwargs)
    return wrapper


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register new user."""
    data = request.get_json() or {}
    name = sanitize_input(data.get("name", ""), 100)
    email = sanitize_input(data.get("email", ""), 200).lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return error_response("Name, email and password are required")

    if not validate_email(email):
        return error_response("Invalid email format")

    valid, msg = validate_password(password)
    if not valid:
        return error_response(msg)

    if UserModel.find_by_email(email):
        return error_response("Email already registered", 409)

    user = UserModel.create({
        "name": name,
        "email": email,
        "password": hash_password(password),
    })

    user.pop("password", None)
    access_token = create_access_token(identity=str(user["_id"]))
    refresh_token = create_refresh_token(identity=str(user["_id"]))

    ActivityLogModel.log(str(user["_id"]), "register", "User registered", "auth")

    return success_response({
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token
    }, "Registration successful", 201)


@auth_bp.route("/login", methods=["POST"])
def login():
    """User login."""
    data = request.get_json() or {}
    email = sanitize_input(data.get("email", ""), 200).lower()
    password = data.get("password", "")

    if not email or not password:
        return error_response("Email and password are required")

    user = UserModel.find_by_email(email)
    if not user or not verify_password(password, user.get("password", "")):
        return error_response("Invalid email or password", 401)

    if not user.get("is_active", True):
        return error_response("Account is deactivated", 403)

    user_data = serialize_doc(user)
    user_data.pop("password", None)

    access_token = create_access_token(identity=str(user["_id"]))
    refresh_token = create_refresh_token(identity=str(user["_id"]))

    ActivityLogModel.log(str(user["_id"]), "login", "User logged in", "auth")

    return success_response({
        "user": user_data,
        "access_token": access_token,
        "refresh_token": refresh_token
    }, "Login successful")


@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    """Admin login."""
    data = request.get_json() or {}
    email = sanitize_input(data.get("email", ""), 200).lower()
    password = data.get("password", "")

    user = UserModel.find_by_email(email)
    if not user or user.get("role") != "admin":
        return error_response("Invalid admin credentials", 401)

    if not verify_password(password, user.get("password", "")):
        return error_response("Invalid admin credentials", 401)

    user_data = serialize_doc(user)
    user_data.pop("password", None)

    access_token = create_access_token(identity=str(user["_id"]))
    refresh_token = create_refresh_token(identity=str(user["_id"]))

    return success_response({
        "user": user_data,
        "access_token": access_token,
        "refresh_token": refresh_token
    }, "Admin login successful")


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Send OTP for password reset."""
    data = request.get_json() or {}
    email = sanitize_input(data.get("email", ""), 200).lower()

    if not validate_email(email):
        return error_response("Invalid email format")

    user = UserModel.find_by_email(email)
    if not user:
        # Don't reveal if email exists
        return success_response({"otp_sent": True}, "If email exists, OTP has been sent")

    otp = generate_otp()
    UserModel.update_otp(email, otp, otp_expiry(10))

    # In production, send OTP via email/SMS
    return success_response({
        "otp_sent": True,
        "otp": otp  # Demo only - remove in production
    }, "OTP sent to your email")


@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    """Verify OTP for password reset."""
    data = request.get_json() or {}
    email = sanitize_input(data.get("email", ""), 200).lower()
    otp = data.get("otp", "")

    if not email or not otp:
        return error_response("Email and OTP are required")

    if not UserModel.verify_otp(email, otp):
        return error_response("Invalid or expired OTP", 400)

    return success_response({"verified": True}, "OTP verified successfully")


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """Reset password after OTP verification."""
    data = request.get_json() or {}
    email = sanitize_input(data.get("email", ""), 200).lower()
    otp = data.get("otp", "")
    new_password = data.get("password", "")

    if not UserModel.verify_otp(email, otp):
        return error_response("Invalid or expired OTP", 400)

    valid, msg = validate_password(new_password)
    if not valid:
        return error_response(msg)

    user = UserModel.find_by_email(email)
    if not user:
        return error_response("User not found", 404)

    UserModel.update(str(user["_id"]), {"password": hash_password(new_password)})
    UserModel.clear_otp(email)

    return success_response(None, "Password reset successful")


@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Get user profile."""
    user_id = get_jwt_identity()
    user = UserModel.find_by_id(user_id)
    if not user:
        return error_response("User not found", 404)

    user_data = serialize_doc(user)
    user_data.pop("password", None)
    user_data.pop("reset_otp", None)
    user_data.pop("reset_otp_expiry", None)
    return success_response(user_data)


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """Update user profile."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    allowed = {"name", "phone", "bio", "avatar"}
    update_data = {k: sanitize_input(str(v), 500) if isinstance(v, str) else v
                   for k, v in data.items() if k in allowed}

    if not update_data:
        return error_response("No valid fields to update")

    UserModel.update(user_id, update_data)

    user = UserModel.find_by_id(user_id)
    user_data = serialize_doc(user)
    user_data.pop("password", None)
    user_data.pop("reset_otp", None)
    user_data.pop("reset_otp_expiry", None)
    return success_response(user_data, "Profile updated")


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """Change password for authenticated user."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return error_response("Current password and new password are required")

    user = UserModel.find_by_id(user_id)
    if not user:
        return error_response("User not found", 404)

    if not verify_password(current_password, user.get("password", "")):
        return error_response("Current password is incorrect", 401)

    valid, msg = validate_password(new_password)
    if not valid:
        return error_response(msg)

    UserModel.update(user_id, {"password": hash_password(new_password)})
    ActivityLogModel.log(user_id, "change_password", "User changed password", "auth")
    return success_response(None, "Password changed successfully")


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return success_response({"access_token": access_token})
