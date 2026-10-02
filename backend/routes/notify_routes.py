"""Notification and Report routes."""
import os

from flask import Blueprint, current_app, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required

from models.notification_model import NotificationModel
from models.threat_model import ThreatReportModel
from models.user_model import UserModel
from routes.auth_routes import admin_required
from services.report_service import ReportService
from utils.response import error_response, success_response

notify_bp = Blueprint("notify", __name__, url_prefix="/api")


@notify_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    """Get user notifications."""
    user_id = get_jwt_identity()
    page = int(request.args.get("page", 1))
    result = NotificationModel.get_for_user(user_id, page)
    unread = NotificationModel.get_unread_count(user_id)
    result["unread_count"] = unread
    return success_response(result)


@notify_bp.route("/notifications/<notification_id>/read", methods=["POST"])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark notification as read."""
    NotificationModel.mark_read(notification_id)
    return success_response(None, "Marked as read")


@notify_bp.route("/notifications/read-all", methods=["POST"])
@jwt_required()
def mark_all_read():
    """Mark all notifications as read."""
    user_id = get_jwt_identity()
    count = NotificationModel.mark_all_read(user_id)
    return success_response({"marked": count})


# ---- REPORTS ----
@notify_bp.route("/reports", methods=["GET"])
@jwt_required()
def get_reports():
    """Get user's threat reports."""
    user_id = get_jwt_identity()
    page = int(request.args.get("page", 1))
    result = ThreatReportModel.find_by_user(user_id, page)
    return success_response(result)


@notify_bp.route("/reports/<report_id>", methods=["GET"])
@jwt_required()
def get_report(report_id):
    """Get single report."""
    report = ThreatReportModel.find_by_id(report_id)
    if not report:
        return error_response("Report not found", 404)
    return success_response(report)


@notify_bp.route("/reports/generate/pdf", methods=["POST"])
@jwt_required()
def generate_pdf_report():
    """Generate PDF report."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    report_id = data.get("report_id")

    if report_id:
        report = ThreatReportModel.find_by_id(report_id)
    else:
        report = data.get("report_data")

    if not report:
        return error_response("Report data required")

    user = UserModel.find_by_id(user_id)
    user_name = user.get("name", "User") if user else "User"

    service = ReportService(current_app.config["REPORTS_FOLDER"])
    filename = service.generate_pdf(report, user_name)

    return success_response({
        "filename": filename,
        "download_url": f"/api/reports/download/{filename}"
    })


@notify_bp.route("/reports/generate/excel", methods=["POST"])
@jwt_required()
def generate_excel_report():
    """Generate Excel report from all user reports."""
    user_id = get_jwt_identity()
    result = ThreatReportModel.find_by_user(user_id, 1, 100)
    reports = result.get("items", [])

    user = UserModel.find_by_id(user_id)
    user_name = user.get("name", "User") if user else "User"

    service = ReportService(current_app.config["REPORTS_FOLDER"])
    filename = service.generate_excel(reports, user_name)

    return success_response({
        "filename": filename,
        "download_url": f"/api/reports/download/{filename}"
    })


@notify_bp.route("/reports/download/<filename>", methods=["GET"])
@jwt_required()
def download_report(filename):
    """Download generated report file."""
    return send_from_directory(current_app.config["REPORTS_FOLDER"], filename, as_attachment=True)
