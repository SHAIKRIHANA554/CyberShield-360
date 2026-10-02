"""Scanner API routes - Image, URL, Email, SMS, QR, OCR."""
import os

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models.activity_model import ActivityLogModel
from models.threat_model import ThreatReportModel
from services.ml_models.image_scanner import ImageScannerService
from services.ml_models.text_analyzer import TextAnalyzerService
from services.ml_models.url_scanner import URLScannerService
from utils.response import error_response, success_response
from utils.validators import allowed_file, sanitize_input, validate_url

scanner_bp = Blueprint("scanner", __name__, url_prefix="/api/scanner")

_url_scanner = None
_text_analyzer = None
_image_scanner = None


def get_url_scanner():
    global _url_scanner
    if _url_scanner is None:
        _url_scanner = URLScannerService(current_app.config.get("URL_MODEL_PATH"))
    return _url_scanner


def get_text_analyzer():
    global _text_analyzer
    if _text_analyzer is None:
        _text_analyzer = TextAnalyzerService()
    return _text_analyzer


def get_image_scanner():
    global _image_scanner
    if _image_scanner is None:
        _image_scanner = ImageScannerService(current_app.config["UPLOAD_FOLDER"])
    return _image_scanner


def save_threat_report(user_id: str, scan_type: str, result: dict) -> dict:
    """Save scan result as a threat report for both registered users and guest checks."""
    try:
        payload = {
            "user_id": user_id or "guest",
            "scan_type": scan_type,
            "threat_level": result.get("threat_level", "unknown"),
            "confidence": result.get("confidence", 0),
            "threat_type": result.get("threat_type", "Unknown"),
            "reasons": result.get("reasons", []),
            "recommendation": result.get("recommendation", ""),
            "details": result
        }
        report = ThreatReportModel.create(payload)
        if user_id:
            ActivityLogModel.log(user_id, f"scan_{scan_type}", f"Threat level: {result.get('threat_level')}", scan_type)
        return report or {"_id": None}
    except Exception as e:
        print(f"Warning: Failed to save threat report: {e}")
        return {"_id": None}


@scanner_bp.route("/url", methods=["POST"])
@jwt_required(optional=True)
def scan_url():
    """Scan URL for phishing/malicious content."""
    data = request.get_json() or {}
    url = sanitize_input(data.get("url", ""), 2000)

    if not url:
        return error_response("URL is required")
    if not validate_url(url):
        return error_response("Invalid URL format")

    user_id = get_jwt_identity()
    result = get_url_scanner().analyze(url)
    report = save_threat_report(user_id, "url", result)

    return success_response({**result, "report_id": report.get("_id")})


@scanner_bp.route("/email", methods=["POST"])
@jwt_required(optional=True)
def scan_email():
    """Scan email for phishing/spam."""
    data = request.get_json() or {}
    content = sanitize_input(data.get("content", ""), 50000)
    sender = sanitize_input(data.get("sender", ""), 200)

    if not content:
        return error_response("Email content is required")

    user_id = get_jwt_identity()
    result = get_text_analyzer().analyze_email(content, sender)
    report = save_threat_report(user_id, "email", result)

    return success_response({**result, "report_id": report.get("_id")})


@scanner_bp.route("/sms", methods=["POST"])
@jwt_required(optional=True)
def scan_sms():
    """Scan SMS/message for scams."""
    data = request.get_json() or {}
    message = sanitize_input(data.get("message", ""), 5000)

    if not message:
        return error_response("Message is required")

    user_id = get_jwt_identity()
    result = get_text_analyzer().analyze_sms(message)
    report = save_threat_report(user_id, "sms", result)

    return success_response({**result, "report_id": report.get("_id")})


@scanner_bp.route("/image", methods=["POST"])
@jwt_required(optional=True)
def scan_image():
    """Scan uploaded image for threats."""
    if "image" not in request.files:
        return error_response("Image file is required")

    file = request.files["image"]
    if not file.filename:
        return error_response("No file selected")

    allowed_ext = current_app.config["ALLOWED_EXTENSIONS"]
    if not allowed_file(file.filename, allowed_ext):
        return error_response(f"Allowed formats: {', '.join(allowed_ext)}")

    user_id = get_jwt_identity()
    scanner = get_image_scanner()
    filepath = scanner.save_image(file, file.filename)
    result = scanner.analyze_image(filepath)
    result["image_path"] = os.path.basename(filepath)
    report = save_threat_report(user_id, "image", result)

    return success_response({**result, "report_id": report.get("_id")})


@scanner_bp.route("/qr", methods=["POST"])
@jwt_required(optional=True)
def scan_qr():
    """Scan QR code from image."""
    if "image" not in request.files:
        # Also accept QR data as text
        data = request.get_json() or {}
        qr_data = data.get("qr_data", "")
        if qr_data:
            user_id = get_jwt_identity()
            result = get_url_scanner().analyze(qr_data)
            result["qr_detected"] = True
            result["qr_data"] = qr_data
            report = save_threat_report(user_id, "qr", result)
            return success_response({**result, "report_id": report.get("_id")})
        return error_response("Image file or QR data is required")

    file = request.files["image"]
    allowed_ext = current_app.config["ALLOWED_EXTENSIONS"]
    if not allowed_file(file.filename, allowed_ext):
        return error_response("Invalid file format")

    user_id = get_jwt_identity()
    scanner = get_image_scanner()
    filepath = scanner.save_image(file, file.filename)
    result = scanner.scan_qr(filepath)
    report = save_threat_report(user_id, "qr", result)

    return success_response({**result, "report_id": report.get("_id")})


@scanner_bp.route("/ocr", methods=["POST"])
@jwt_required(optional=True)
def scan_ocr():
    """Extract and analyze text from image using OCR."""
    if "image" not in request.files:
        return error_response("Image file is required")

    file = request.files["image"]
    allowed_ext = current_app.config["ALLOWED_EXTENSIONS"]
    if not allowed_file(file.filename, allowed_ext):
        return error_response("Invalid file format")

    user_id = get_jwt_identity()
    scanner = get_image_scanner()
    filepath = scanner.save_image(file, file.filename)
    ocr_result = scanner.extract_text_ocr(filepath)

    # Analyze extracted text
    text = ocr_result.get("text", "")
    text_result = get_text_analyzer().analyze_sms(text) if text else {
        "threat_level": "safe", "confidence": 0.5, "threat_type": "None",
        "reasons": ["No text extracted"], "recommendation": "Upload clearer image"
    }

    result = {
        **ocr_result,
        "threat_level": text_result.get("threat_level"),
        "confidence": text_result.get("confidence"),
        "threat_type": text_result.get("threat_type"),
        "reasons": text_result.get("reasons", []),
        "recommendation": text_result.get("recommendation", ""),
        "model": "EasyOCR + ML Threat Analysis"
    }

    report = save_threat_report(user_id, "ocr", result)
    return success_response({**result, "report_id": report.get("_id")})


@scanner_bp.route("/fake-image", methods=["POST"])
@jwt_required(optional=True)
def scan_fake_image():
    """Detect fake banking screenshots and scam images."""
    if "image" not in request.files:
        return error_response("Image file is required")

    file = request.files["image"]
    allowed_ext = current_app.config["ALLOWED_EXTENSIONS"]
    if not allowed_file(file.filename, allowed_ext):
        return error_response("Invalid file format")

    user_id = get_jwt_identity()
    scanner = get_image_scanner()
    filepath = scanner.save_image(file, file.filename)
    result = scanner.analyze_image(filepath)

    # Enhance for fake image detection
    fake_types = ["Fake Banking Screenshot", "Lottery Poster", "Scam Advertisement",
                  "Fraud Image", "Payment App Interface", "Banking App Interface"]
    detected_fakes = [d for d in result.get("detections", []) if d.get("label") in fake_types]

    if detected_fakes:
        result["threat_level"] = "danger"
        result["threat_type"] = detected_fakes[0].get("label", "Fake Image")
        result["confidence"] = max(result.get("confidence", 0), 0.85)

    report = save_threat_report(user_id, "fake_image", result)
    return success_response({**result, "report_id": report.get("_id")})
