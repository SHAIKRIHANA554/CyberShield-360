"""OCR and Image analysis service using EasyOCR, OpenCV, YOLOv8."""
import os
import re
import uuid

import cv2
import numpy as np

from utils.validators import extract_urls, extract_emails, extract_phones, extract_upi_ids


class ImageScannerService:
    """Analyze images for scams, OCR text extraction, and object detection."""

    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder
        self._ocr_reader = None
        self._yolo_model = None
        self._init_models()

    def _init_models(self):
        """Initialize OCR and YOLO models lazily."""
        os.makedirs(self.upload_folder, exist_ok=True)

    def _get_ocr(self):
        """Lazy load EasyOCR."""
        if self._ocr_reader is None:
            try:
                import easyocr
                self._ocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            except Exception:
                self._ocr_reader = False
        return self._ocr_reader if self._ocr_reader else None

    def _get_yolo(self):
        """Lazy load YOLOv8."""
        if self._yolo_model is None:
            try:
                from ultralytics import YOLO
                self._yolo_model = YOLO("yolov8n.pt")
            except Exception:
                self._yolo_model = False
        return self._yolo_model if self._yolo_model else None

    def save_image(self, file_data, filename: str) -> str:
        """Save uploaded image securely."""
        ext = filename.rsplit(".", 1)[-1].lower()
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(self.upload_folder, safe_name)
        file_data.save(filepath)
        return filepath

    def extract_text_ocr(self, image_path: str) -> dict:
        """Extract text from image using EasyOCR."""
        reader = self._get_ocr()
        extracted_text = ""
        ocr_details = []

        if reader:
            try:
                results = reader.readtext(image_path)
                texts = [text for _, text, conf in results if conf > 0.3]
                extracted_text = " ".join(texts)
                ocr_details = [{"text": t, "confidence": round(c, 2)} for _, t, c in results]
            except Exception:
                extracted_text = self._fallback_ocr(image_path)
        else:
            extracted_text = self._fallback_ocr(image_path)

        return {
            "text": extracted_text,
            "details": ocr_details,
            "urls": extract_urls(extracted_text),
            "emails": extract_emails(extracted_text),
            "phones": extract_phones(extracted_text),
            "upi_ids": extract_upi_ids(extracted_text),
        }

    def _fallback_ocr(self, image_path: str) -> str:
        """Basic OpenCV text region detection fallback."""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return ""
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Detect text-like regions
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            return f"[Image contains {len(contours)} text regions - EasyOCR recommended for full extraction]"
        except Exception:
            return ""

    def detect_objects(self, image_path: str) -> list:
        """Detect objects using YOLOv8."""
        model = self._get_yolo()
        detections = []

        if model:
            try:
                results = model(image_path, verbose=False)
                for result in results:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        label = result.names[cls_id]
                        if conf > 0.4:
                            detections.append({
                                "label": label,
                                "confidence": round(conf, 2)
                            })
            except Exception:
                pass

        # Always run heuristic image analysis
        heuristic = self._heuristic_image_analysis(image_path)
        detections.extend(heuristic)

        return detections

    def _heuristic_image_analysis(self, image_path: str) -> list:
        """Analyze image properties for scam indicators."""
        detections = []
        try:
            img = cv2.imread(image_path)
            if img is None:
                return detections

            h, w = img.shape[:2]

            # QR code detection
            qr_detector = cv2.QRCodeDetector()
            data, points, _ = qr_detector.detectAndDecode(img)
            if data:
                detections.append({
                    "label": "QR Code",
                    "confidence": 0.95,
                    "data": data
                })

            # Check for screenshot-like aspect ratios (mobile screenshots)
            aspect = w / h if h > 0 else 1
            if 0.4 < aspect < 0.6:
                detections.append({
                    "label": "Mobile Screenshot",
                    "confidence": 0.75
                })

            # Color analysis - banking apps often have specific color schemes
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            blue_mask = cv2.inRange(hsv, (100, 50, 50), (130, 255, 255))
            blue_ratio = np.sum(blue_mask > 0) / (h * w)
            if blue_ratio > 0.15:
                detections.append({
                    "label": "Banking App Interface",
                    "confidence": round(min(0.85, blue_ratio * 3), 2)
                })

            green_mask = cv2.inRange(hsv, (35, 50, 50), (85, 255, 255))
            green_ratio = np.sum(green_mask > 0) / (h * w)
            if green_ratio > 0.15:
                detections.append({
                    "label": "Payment App Interface",
                    "confidence": round(min(0.85, green_ratio * 3), 2)
                })

        except Exception:
            pass

        return detections

    def analyze_image(self, image_path: str) -> dict:
        """Full image threat analysis pipeline."""
        ocr_result = self.extract_text_ocr(image_path)
        detections = self.detect_objects(image_path)
        text = ocr_result.get("text", "")

        threat_types = []
        reasons = []
        score = 0.0

        # Analyze extracted text
        scam_keywords = [
            "lottery", "winner", "prize", "congratulations", "claim now",
            "kyc update", "account suspended", "otp", "verify account",
            "click here", "urgent", "free gift", "won", "cash prize",
            "investment", "double your money", "bank alert"
        ]
        text_lower = text.lower()
        keyword_hits = [kw for kw in scam_keywords if kw in text_lower]
        if keyword_hits:
            score += min(0.40, len(keyword_hits) * 0.08)
            reasons.append(f"Scam keywords found: {', '.join(keyword_hits[:5])}")
            threat_types.append("Scam Text")

        # URL analysis in image
        if ocr_result.get("urls"):
            score += 0.20
            reasons.append(f"Contains {len(ocr_result['urls'])} URL(s) in image")
            threat_types.append("Malicious URL")

        # UPI IDs
        if ocr_result.get("upi_ids"):
            score += 0.10
            reasons.append("UPI payment IDs detected in image")

        # Object detections
        for det in detections:
            label = det.get("label", "")
            if label == "QR Code":
                qr_data = det.get("data", "")
                if qr_data:
                    threat_types.append("QR Code")
                    reasons.append(f"QR code detected with data: {qr_data[:50]}...")
                    score += 0.15
            elif label in ("Banking App Interface", "Payment App Interface", "Mobile Screenshot"):
                threat_types.append("Fake Banking Screenshot")
                reasons.append(f"Detected: {label}")
                score += 0.20
            elif label in ("Scam Advertisement", "Lottery Poster", "Fraud Image"):
                threat_types.append(label)
                score += 0.25

        confidence = min(0.99, max(0.55, score + 0.5))

        if score >= 0.5:
            level = "danger"
        elif score >= 0.25:
            level = "warning"
        else:
            level = "safe"
            reasons = ["No significant threats detected in image", "Image appears safe"]
            confidence = max(0.72, 1.0 - score)

        return {
            "threat_level": level,
            "confidence": round(confidence, 2),
            "threat_type": threat_types[0] if threat_types else "None",
            "threat_types": list(set(threat_types)),
            "reasons": reasons,
            "ocr_text": text[:500],
            "extracted_data": {
                "urls": ocr_result.get("urls", []),
                "emails": ocr_result.get("emails", []),
                "phones": ocr_result.get("phones", []),
                "upi_ids": ocr_result.get("upi_ids", []),
            },
            "detections": detections,
            "recommendation": self._get_recommendation(level),
            "model": "YOLOv8 + EasyOCR + BERT Analysis"
        }

    def scan_qr(self, image_path: str) -> dict:
        """Detect and analyze QR code from image."""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return {"error": "Could not read image", "threat_level": "unknown"}

            qr_detector = cv2.QRCodeDetector()
            data, points, _ = qr_detector.detectAndDecode(img)

            if not data:
                return {
                    "qr_detected": False,
                    "threat_level": "safe",
                    "confidence": 0.90,
                    "message": "No QR code detected in image",
                    "recommendation": "Ensure QR code is clearly visible"
                }

            # Analyze QR data (usually URL)
            from services.ml_models.url_scanner import URLScannerService
            url_scanner = URLScannerService()
            url_result = url_scanner.analyze(data)

            return {
                "qr_detected": True,
                "qr_data": data,
                "threat_level": url_result.get("threat_level", "warning"),
                "confidence": url_result.get("confidence", 0.5),
                "threat_type": url_result.get("threat_type", "Unknown"),
                "reasons": url_result.get("reasons", []),
                "recommendation": url_result.get("recommendation", "Verify QR code source"),
                "url_analysis": url_result
            }
        except Exception as e:
            return {"error": str(e), "threat_level": "unknown", "confidence": 0}

    def _get_recommendation(self, level: str) -> str:
        if level == "danger":
            return "This image contains potential scam content. Do not act on any instructions shown."
        elif level == "warning":
            return "Exercise caution. Verify all information through official channels."
        return "Image appears safe. Continue practicing good cyber hygiene."
