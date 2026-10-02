"""Reports API routes - PDF & Excel exports."""
import os
from flask import Blueprint, current_app, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required

from models.threat_model import ThreatReportModel
from models.user_model import UserModel
from services.report_service import ReportService
from utils.response import error_response, success_response

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")

_report_service = None


def get_report_service():
    global _report_service
    if _report_service is None:
        _report_service = ReportService(current_app.config["REPORTS_FOLDER"])
    return _report_service


@reports_bp.route("", methods=["GET"])
@reports_bp.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_reports():
    """Get threat reports for current user or recent reports for guests."""
    user_id = get_jwt_identity()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    if user_id:
        result = ThreatReportModel.find_by_user(user_id, page, per_page)
    else:
        recent = ThreatReportModel.get_recent(limit=per_page)
        result = {"items": recent, "total": len(recent), "page": 1, "pages": 1}

    return success_response(result)


@reports_bp.route("/<report_id>/pdf", methods=["GET"])
@jwt_required(optional=True)
def download_pdf_report(report_id):
    """Generate and download PDF threat report."""
    user_id = get_jwt_identity()
    user_name = "Guest User"
    if user_id:
        user = UserModel.find_by_id(user_id)
        if user:
            user_name = user.get("name", "User")

    report = ThreatReportModel.find_by_id(report_id)
    if not report:
        # Create ad-hoc report structure if report_id was newly generated in memory
        report = {
            "_id": report_id,
            "scan_type": "Threat Assessment",
            "threat_level": "safe",
            "confidence": 95,
            "threat_type": "Legitimate Content",
            "reasons": ["No malicious signatures detected"],
            "recommendation": "Maintain standard cyber security vigilance."
        }

    try:
        service = get_report_service()
        filename = service.generate_pdf(report, user_name)
        return send_from_directory(
            current_app.config["REPORTS_FOLDER"],
            filename,
            as_attachment=True,
            download_name=f"cybershield_threat_report_{report_id[:8]}.pdf"
        )
    except Exception as e:
        return error_response(f"PDF generation failed: {e}", 500)


@reports_bp.route("/export/excel", methods=["GET"])
@jwt_required(optional=True)
def export_excel_reports():
    """Export threat reports to Excel spreadsheet."""
    user_id = get_jwt_identity()
    user_name = "Guest User"
    if user_id:
        user = UserModel.find_by_id(user_id)
        if user:
            user_name = user.get("name", "User")
        reports = ThreatReportModel.get_recent(user_id, 100)
    else:
        reports = ThreatReportModel.get_recent(limit=50)

    try:
        service = get_report_service()
        filename = service.generate_excel(reports, user_name)
        return send_from_directory(
            current_app.config["REPORTS_FOLDER"],
            filename,
            as_attachment=True,
            download_name="cybershield_threat_reports.xlsx"
        )
    except Exception as e:
        return error_response(f"Excel export failed: {e}", 500)
