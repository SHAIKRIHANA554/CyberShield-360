"""Standardized API response helpers."""
from flask import jsonify


def success_response(data=None, message: str = "Success", status: int = 200):
    """Return success JSON response."""
    response = {"success": True, "message": message}
    if data is not None:
        response["data"] = data
    return jsonify(response), status


def error_response(message: str = "An error occurred", status: int = 400, errors=None):
    """Return error JSON response."""
    response = {"success": False, "message": message}
    if errors:
        response["errors"] = errors
    return jsonify(response), status
