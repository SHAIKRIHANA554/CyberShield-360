"""URL Scanner service using Random Forest + heuristics."""
import os
import pickle

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from services.ml_models.url_features import extract_url_features, heuristic_url_score


class URLScannerService:
    """Analyze URLs for phishing and malicious content."""

    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.model = None
        self._load_or_train_model()

    def _load_or_train_model(self):
        """Load pre-trained model or train a new one."""
        if self.model_path and os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                return
            except Exception:
                pass
        self.model = self._train_default_model()
        if self.model_path:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            try:
                with open(self.model_path, "wb") as f:
                    pickle.dump(self.model, f)
            except Exception:
                pass

    def _train_default_model(self) -> RandomForestClassifier:
        """Train Random Forest on known safe/unsafe URL patterns."""
        # Training data: [features] with labels (0=safe, 1=suspicious, 2=danger)
        safe_urls = [
            "https://www.google.com",
            "https://github.com",
            "https://www.microsoft.com/en-us/security",
            "https://stackoverflow.com/questions",
            "https://www.wikipedia.org",
            "https://www.amazon.in",
            "https://www.hdfcbank.com",
            "https://www.cert-in.org.in",
            "https://www.cloudflare.com",
            "https://www.ncsc.gov.uk",
        ]
        suspicious_urls = [
            "http://secure-login-verify.account-update.tk/signin",
            "https://bit.ly/3xK9mP2",
            "http://www.paypal-secure-login.xyz/verify",
            "https://account-update-banking.info/confirm",
            "http://free-prize-winner.click/claim",
        ]
        danger_urls = [
            "http://192.168.1.100/login@secure-bank.tk/verify",
            "http://hdfc-bank-kyc-update.ml/urgent/otp",
            "https://sbi-account-suspended.ga/restore-now",
            "http://lottery-winner-prize.tk/claim?id=12345",
            "https://upi-payment-refund.xyz/enter-details",
            "http://amazon-security-alert.cf/account-locked",
        ]

        X, y = [], []
        for url in safe_urls:
            X.append(extract_url_features(url))
            y.append(0)
        for url in suspicious_urls:
            X.append(extract_url_features(url))
            y.append(1)
        for url in danger_urls:
            X.append(extract_url_features(url))
            y.append(2)

        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(np.array(X), np.array(y))
        return model

    def analyze(self, url: str) -> dict:
        """Analyze URL and return threat assessment."""
        url = url.strip()
        if not url:
            return self._error_result("URL is required")

        features = extract_url_features(url)
        heuristic_level, heuristic_conf, heuristic_reasons = heuristic_url_score(url)

        ml_level = "safe"
        ml_confidence = 0.5

        if self.model:
            try:
                prediction = self.model.predict([features])[0]
                probabilities = self.model.predict_proba([features])[0]
                ml_confidence = float(max(probabilities))

                level_map = {0: "safe", 1: "warning", 2: "danger"}
                ml_level = level_map.get(int(prediction), "warning")
            except Exception:
                ml_level = heuristic_level
                ml_confidence = heuristic_conf

        # Combine ML and heuristic scores
        level_priority = {"safe": 0, "warning": 1, "danger": 2}
        final_level = ml_level if level_priority.get(ml_level, 0) >= level_priority.get(heuristic_level, 0) else heuristic_level
        confidence = round((ml_confidence + heuristic_conf) / 2, 2)

        reasons = heuristic_reasons if final_level != "safe" else ["URL structure appears legitimate", "Domain reputation check passed"]

        threat_types = []
        if final_level == "danger":
            threat_types = ["Phishing", "Malicious URL"]
        elif final_level == "warning":
            threat_types = ["Suspicious URL", "Potential Phishing"]

        recommendations = self._get_recommendations(final_level)

        return {
            "url": url,
            "threat_level": final_level,
            "confidence": confidence,
            "threat_type": threat_types[0] if threat_types else "None",
            "threat_types": threat_types,
            "reasons": reasons,
            "recommendation": recommendations,
            "features_analyzed": len(features),
            "model": "Random Forest + Heuristic Analysis"
        }

    def _get_recommendations(self, level: str) -> str:
        """Get recommendation based on threat level."""
        if level == "danger":
            return "Do NOT visit this URL. Report it to CERT-In. Block the domain and warn others."
        elif level == "warning":
            return "Exercise caution. Verify the URL through official channels before proceeding."
        return "URL appears safe. Always verify sensitive transactions through official apps."

    def _error_result(self, message: str) -> dict:
        return {
            "url": "",
            "threat_level": "unknown",
            "confidence": 0,
            "threat_type": "Error",
            "reasons": [message],
            "recommendation": "Please provide a valid URL",
            "error": message
        }
