"""Text analysis service using NLP patterns + keyword heuristics + ML model."""
import os
import pickle
import re


# ============================================================
# SCAM PATTERNS
# ============================================================

OTP_SCAM_PATTERNS = [
    r"otp.*share",
    r"share.*otp",
    r"never share.*otp",
    r"otp.*call",
    r"verify.*otp.*immediately",
    r"your otp is",
    r"otp.*expir",
    r"send.*otp",
    r"tell.*otp",
]

BANK_SCAM_PATTERNS = [
    r"account.*suspend",
    r"block.*account",
    r"kyc.*update",
    r"kyc.*expir",
    r"bank.*verif",
    r"debit card.*block",
    r"credit card.*compromis",
    r"unusual.*activit",
    r"click.*link.*verify",
    r"update.*pan.*card",
    r"bank.*account.*verify",
    r"account.*verification",
]

LOTTERY_SCAM_PATTERNS = [
    r"congratulation.*won",
    r"you.*winner",
    r"claim.*prize",
    r"lottery.*winner",
    r"lucky.*draw",
    r"free.*gift",
    r"won.*\d+.*lakh",
    r"won.*\d+.*crore",
    r"prize.*claim",
]

INVESTMENT_FRAUD_PATTERNS = [
    r"guaranteed.*return",
    r"double.*money",
    r"invest.*\d+%.*return",
    r"crypto.*profit",
    r"forex.*trading.*profit",
    r"get rich quick",
    r"guaranteed.*profit",
    r"risk.?free.*investment",
]

SOCIAL_ENGINEERING_PATTERNS = [
    r"urgent.*action",
    r"immediate.*attention",
    r"act now",
    r"limited time",
    r"limited.*position",
    r"limited.*opening",
    r"your.*package.*held",
    r"customs.*fee",
    r"tax.*refund",
    r"irs.*notice",
    r"final.*warning",
    r"account.*will.*close",
]

PHISHING_EMAIL_PATTERNS = [
    r"dear customer",
    r"dear user",
    r"verify your account",
    r"confirm your identity",
    r"unusual sign.?in",
    r"password.*expir",
    r"security alert",
    r"suspended.*account",
]

# ------------------------------------------------------------
# NEW: JOB / WORK-FROM-HOME SCAM PATTERNS
# ------------------------------------------------------------

JOB_SCAM_PATTERNS = [
    r"work.?from.?home",
    r"remote.*job",
    r"online.*job",
    r"part.?time.*job",
    r"data.?entry.*job",
    r"earn.*\d+.*(?:per day|daily|month)",
    r"earn.*₹?\s*\d+",
    r"salary.*₹?\s*\d+",
    r"no experience.*required",
    r"no experience.*needed",
    r"security deposit",
    r"refundable.*deposit",
    r"registration fee",
    r"joining fee",
    r"onboarding fee",
    r"activation fee",
    r"training fee",
    r"processing fee.*job",
    r"pay.*before.*work",
    r"payment.*required.*(?:activate|access|join)",
    r"employee.*account.*(?:activation|activate)",
    r"task dashboard.*unlock",
    r"limited.*(?:position|vacancy|opening)",
]

# ------------------------------------------------------------
# NEW: REFUND / PAYMENT SCAM PATTERNS
# ------------------------------------------------------------

REFUND_SCAM_PATTERNS = [
    r"refund.*(?:pending|verification|verify)",
    r"verify.*refund",
    r"refund.*(?:details|account|bank)",
    r"refund.*(?:within|before).*minute",
    r"complete.*verification.*refund",
    r"pay.*(?:fee|charge).*refund",
    r"refund.*link",
    r"confirm.*details.*refund",
    r"refund.*(?:claim|receive)",
    r"refund.*(?:cancel|expire)",
    r"refund.*(?:otp|password)",
]

# ------------------------------------------------------------
# NEW: PAYMENT / MONEY REQUEST PATTERNS
# ------------------------------------------------------------

PAYMENT_SCAM_PATTERNS = [
    r"pay.*(?:fee|charge|deposit)",
    r"payment.*required",
    r"make.*payment.*(?:now|immediately)",
    r"pay.*within.*(?:minute|hour)",
    r"processing fee",
    r"verification fee",
    r"security fee",
    r"account activation.*payment",
    r"send.*money.*(?:now|today)",
    r"transfer.*(?:₹|rs\.?|inr)",
    r"pay.*₹?\s*\d+",
]

URGENT_WORDS = [
    "urgent",
    "immediately",
    "act now",
    "expire",
    "suspended",
    "blocked",
    "warning",
    "alert",
    "critical",
    "final notice",
    "last chance",
    "limited time",
    "within 30 minutes",
    "within 10 minutes",
    "today only",
]


class TextAnalyzerService:
    """Analyze SMS and emails for scams using patterns and trained ML."""

    def __init__(self, model_path: str = None):
        self._ml_model = None
        self._load_ml_model(model_path)

        # Reserved for future BERT integration
        self._bert_available = False
        self._classifier = None

    # ============================================================
    # MODEL LOADING
    # ============================================================

    def _load_ml_model(self, model_path: str = None):
        """Load trained TF-IDF text threat model."""

        if not model_path:
            base_dir = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(__file__)
                    )
                )
            )

            model_path = os.path.join(
                base_dir,
                "ml_models",
                "text_threat_model.pkl"
            )

        if os.path.exists(model_path):
            try:
                with open(model_path, "rb") as f:
                    self._ml_model = pickle.load(f)

                print("Text threat ML model loaded successfully.")

            except Exception as e:
                print(f"Warning: Could not load text ML model: {e}")

    # ============================================================
    # PATTERN HELPERS
    # ============================================================

    def _match_patterns(self, text: str, patterns: list) -> list:
        """Return all regex patterns that match the text."""

        matches = []
        text_lower = text.lower()

        for pattern in patterns:
            try:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    matches.append(pattern)
            except re.error:
                continue

        return matches

    def _count_urgent_language(self, text: str) -> int:
        """Count urgency/scam trigger words."""

        text_lower = text.lower()

        return sum(
            1
            for word in URGENT_WORDS
            if word in text_lower
        )

    def _contains_money_amount(self, text: str) -> bool:
        """Detect common Indian currency amounts."""

        patterns = [
            r"₹\s*\d+",
            r"rs\.?\s*\d+",
            r"inr\s*\d+",
            r"\d+\s*(?:rupees|rs)",
        ]

        return any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in patterns
        )

    # ============================================================
    # SMS ANALYSIS
    # ============================================================

    def analyze_sms(self, message: str) -> dict:
        """Analyze SMS/message for scam patterns."""

        message = message.strip()

        if not message:
            return self._error_result("Message is required")

        threat_types = []
        reasons = []
        score = 0.0

        # --------------------------------------------------------
        # OTP SCAM
        # --------------------------------------------------------

        if self._match_patterns(
            message,
            OTP_SCAM_PATTERNS
        ):
            threat_types.append("OTP Scam")

            reasons.append(
                "Message requests OTP sharing or verification"
            )

            score += 0.40

        # --------------------------------------------------------
        # BANK SCAM
        # --------------------------------------------------------

        if self._match_patterns(
            message,
            BANK_SCAM_PATTERNS
        ):
            threat_types.append("Bank Scam")

            reasons.append(
                "Contains banking fraud indicators"
            )

            score += 0.35

        # --------------------------------------------------------
        # LOTTERY SCAM
        # --------------------------------------------------------

        if self._match_patterns(
            message,
            LOTTERY_SCAM_PATTERNS
        ):
            threat_types.append("Lottery Scam")

            reasons.append(
                "Lottery/prize winning scam detected"
            )

            score += 0.35

        # --------------------------------------------------------
        # INVESTMENT FRAUD
        # --------------------------------------------------------

        if self._match_patterns(
            message,
            INVESTMENT_FRAUD_PATTERNS
        ):
            threat_types.append("Investment Fraud")

            reasons.append(
                "Unrealistic investment returns promised"
            )

            score += 0.30

        # --------------------------------------------------------
        # SOCIAL ENGINEERING
        # --------------------------------------------------------

        if self._match_patterns(
            message,
            SOCIAL_ENGINEERING_PATTERNS
        ):
            threat_types.append("Social Engineering")

            reasons.append(
                "Social engineering tactics detected"
            )

            score += 0.20

        # --------------------------------------------------------
        # JOB / WFH SCAM
        # --------------------------------------------------------

        job_matches = self._match_patterns(
            message,
            JOB_SCAM_PATTERNS
        )

        if job_matches:
            threat_types.append("Job Scam")

            reasons.append(
                "Work-from-home/job scam indicators detected"
            )

            score += 0.30

        # --------------------------------------------------------
        # REFUND SCAM
        # --------------------------------------------------------

        refund_matches = self._match_patterns(
            message,
            REFUND_SCAM_PATTERNS
        )

        if refund_matches:
            threat_types.append("Refund Scam")

            reasons.append(
                "Suspicious refund/verification indicators detected"
            )

            score += 0.30

        # --------------------------------------------------------
        # PAYMENT SCAM
        # --------------------------------------------------------

        payment_matches = self._match_patterns(
            message,
            PAYMENT_SCAM_PATTERNS
        )

        if payment_matches:
            threat_types.append("Payment Scam")

            reasons.append(
                "Message requests payment, fee, deposit, or money transfer"
            )

            score += 0.25

        # --------------------------------------------------------
        # MONEY + JOB / REFUND COMBINATION
        # --------------------------------------------------------

        has_money = self._contains_money_amount(message)

        if has_money and (
            "Job Scam" in threat_types
            or "Refund Scam" in threat_types
            or "Payment Scam" in threat_types
        ):
            score += 0.15

            reasons.append(
                "Financial amount associated with a suspicious request"
            )

        # --------------------------------------------------------
        # URGENCY
        # --------------------------------------------------------

        urgent_count = self._count_urgent_language(message)

        if urgent_count >= 1:
            score += 0.08

        if urgent_count >= 2:
            score += 0.12

            reasons.append(
                f"Contains {urgent_count} urgency trigger words"
            )

        # --------------------------------------------------------
        # URL DETECTION
        # --------------------------------------------------------

        urls = re.findall(
            r"https?://\S+|www\.\S+",
            message
        )

        if urls:
            score += min(
                0.20,
                len(urls) * 0.10
            )

            reasons.append(
                f"Contains {len(urls)} URL(s) - verify before clicking"
            )

        # --------------------------------------------------------
        # TRAINED ML MODEL
        # --------------------------------------------------------

        ml_prediction = None
        ml_confidence = 0.0

        if self._ml_model:

            try:
                ml_prediction = self._ml_model.predict(
                    [message]
                )[0]

                probas = self._ml_model.predict_proba(
                    [message]
                )[0]

                ml_confidence = float(
                    max(probas)
                )

                if ml_prediction == 2:

                    score += 0.30 * ml_confidence

                    reasons.append(
                        "ML Classifier flagged message as high threat/scam"
                    )

                elif ml_prediction == 1:

                    score += 0.18 * ml_confidence

                    reasons.append(
                        "ML Classifier flagged message as suspicious"
                    )

            except Exception as e:
                print(
                    f"Warning: Text ML prediction failed: {e}"
                )

        # --------------------------------------------------------
        # BERT SUPPLEMENTARY SIGNAL
        # --------------------------------------------------------

        if self._bert_available and self._classifier:

            try:

                result = self._classifier(
                    message[:512]
                )[0]

                if (
                    result["label"] == "NEGATIVE"
                    and result["score"] > 0.7
                ):
                    score += 0.10

                    reasons.append(
                        "NLP sentiment model detected suspicious language"
                    )

            except Exception:
                pass

        # --------------------------------------------------------
        # FINAL CLASSIFICATION
        # --------------------------------------------------------

        score = min(score, 0.99)

        if (
            ("Bank Scam" in threat_types or "Phishing" in threat_types)
            and ("Job Scam" in threat_types or "Refund Scam" in threat_types or "Payment Scam" in threat_types or urls)
        ):
            level = "danger"
        elif score >= 0.65:
            level = "danger"
        elif score >= 0.30:
            level = "warning"
        else:
            level = "safe"

        # --------------------------------------------------------
        # SAFE MESSAGE
        # --------------------------------------------------------

        if level == "safe":

            reasons = [
                "No significant scam indicators detected",
                "Message appears relatively safe based on current rules"
            ]

            confidence = max(
                0.75,
                min(0.95, 1.0 - score)
            )

        else:

            confidence = min(
                0.99,
                max(
                    0.60,
                    0.50 + score
                )
            )

        # --------------------------------------------------------
        # EXTRA SAFETY OVERRIDE
        # --------------------------------------------------------
        # If a message asks for money before providing a job,
        # classify it as at least WARNING.

        financial_job_risk = (
            "Job Scam" in threat_types
            and (
                "Payment Scam" in threat_types
                or "security deposit" in message.lower()
                or "registration fee" in message.lower()
                or "joining fee" in message.lower()
                or "onboarding fee" in message.lower()
                or "activation fee" in message.lower()
            )
        )

        if financial_job_risk:

            if level == "safe":
                level = "warning"

            confidence = max(
                confidence,
                0.88
            )

            if (
                "Upfront payment requested for job access"
                not in reasons
            ):
                reasons.append(
                    "Upfront payment requested for job access"
                )

        # Refund + payment override

        financial_refund_risk = (
            "Refund Scam" in threat_types
            and (
                "Payment Scam" in threat_types
                or "verify" in message.lower()
                or "verification" in message.lower()
                or "bank" in message.lower()
                or "details" in message.lower()
            )
        )

        if financial_refund_risk:

            if level == "safe":
                level = "warning"

            confidence = max(
                confidence,
                0.88
            )

            if (
                "Suspicious refund verification request"
                not in reasons
            ):
                reasons.append(
                    "Suspicious refund verification request"
                )

        return {
            "message": message[:200],
            "threat_level": level,
            "confidence": round(confidence, 2),
            "threat_type": (
                threat_types[0]
                if threat_types
                else "None"
            ),
            "threat_types": list(
                dict.fromkeys(threat_types)
            ),
            "reasons": reasons,
            "recommendation": self._get_recommendation(
                level,
                threat_types
            ),
            "model": "ML + NLP Pattern Analysis",
            "score": round(score, 2),
            "ml_prediction": ml_prediction,
            "ml_confidence": round(
                ml_confidence,
                2
            ),
        }

    # ============================================================
    # EMAIL ANALYSIS
    # ============================================================

    def analyze_email(
        self,
        email_content: str,
        sender: str = ""
    ) -> dict:

        email_content = email_content.strip()

        if not email_content:
            return self._error_result(
                "Email content is required"
            )

        threat_types = []
        reasons = []
        score = 0.0

        # --------------------------------------------------------
        # SENDER ANALYSIS
        # --------------------------------------------------------

        if sender:

            sender_lower = sender.lower()

            if re.search(
                r"@(gmail|yahoo|hotmail|outlook)\.(com|in)",
                sender_lower
            ):

                bank_names = [
                    "hdfc",
                    "sbi",
                    "icici",
                    "axis",
                    "paytm",
                    "phonepe"
                ]

                if any(
                    bank in email_content.lower()
                    for bank in bank_names
                ):

                    score += 0.25

                    reasons.append(
                        "Sender uses free email but claims to be a bank/institution"
                    )

                    threat_types.append(
                        "Phishing"
                    )

        # --------------------------------------------------------
        # PHISHING
        # --------------------------------------------------------

        if self._match_patterns(
            email_content,
            PHISHING_EMAIL_PATTERNS
        ):

            threat_types.append(
                "Phishing"
            )

            reasons.append(
                "Phishing email patterns detected"
            )

            score += 0.30

        # --------------------------------------------------------
        # BANK
        # --------------------------------------------------------

        if self._match_patterns(
            email_content,
            BANK_SCAM_PATTERNS
        ):

            threat_types.append(
                "Bank Scam"
            )

            reasons.append(
                "Banking fraud indicators in email"
            )

            score += 0.25

        # --------------------------------------------------------
        # JOB SCAM
        # --------------------------------------------------------

        if self._match_patterns(
            email_content,
            JOB_SCAM_PATTERNS
        ):

            threat_types.append(
                "Job Scam"
            )

            reasons.append(
                "Work-from-home/job scam indicators detected"
            )

            score += 0.30

        # --------------------------------------------------------
        # REFUND SCAM
        # --------------------------------------------------------

        if self._match_patterns(
            email_content,
            REFUND_SCAM_PATTERNS
        ):

            threat_types.append(
                "Refund Scam"
            )

            reasons.append(
                "Suspicious refund indicators detected"
            )

            score += 0.30

        # --------------------------------------------------------
        # PAYMENT
        # --------------------------------------------------------

        if self._match_patterns(
            email_content,
            PAYMENT_SCAM_PATTERNS
        ):

            threat_types.append(
                "Payment Scam"
            )

            reasons.append(
                "Payment or fee request detected"
            )

            score += 0.25

        # --------------------------------------------------------
        # LINKS
        # --------------------------------------------------------

        urls = re.findall(
            r"https?://\S+|www\.\S+",
            email_content
        )

        if urls:

            reasons.append(
                f"Email contains {len(urls)} link(s)"
            )

            score += min(
                0.20,
                len(urls) * 0.05
            )

        # --------------------------------------------------------
        # ATTACHMENTS
        # --------------------------------------------------------

        if re.search(
            r"attach|download|open.*file|\.exe|\.zip|\.scr",
            email_content,
            re.I
        ):

            threat_types.append(
                "Malware"
            )

            reasons.append(
                "Email references suspicious attachments"
            )

            score += 0.25

        # --------------------------------------------------------
        # URGENCY
        # --------------------------------------------------------

        urgent = self._count_urgent_language(
            email_content
        )

        if urgent >= 1:
            score += 0.08

        if urgent >= 2:

            score += 0.12

            reasons.append(
                "Excessive urgency language detected"
            )

        # --------------------------------------------------------
        # SPAM
        # --------------------------------------------------------

        spam_words = [
            "unsubscribe",
            "click here",
            "limited offer",
            "act now",
            "free"
        ]

        spam_count = sum(
            1
            for word in spam_words
            if word in email_content.lower()
        )

        if spam_count >= 3:

            threat_types.append(
                "Spam"
            )

            score += 0.10

            reasons.append(
                "Multiple spam indicators detected"
            )

        # --------------------------------------------------------
        # FINAL CLASSIFICATION
        # --------------------------------------------------------

        score = min(
            score,
            0.99
        )

        if (
            ("Bank Scam" in threat_types or "Phishing" in threat_types)
            and (
                "Job Scam" in threat_types
                or "Refund Scam" in threat_types
                or "Payment Scam" in threat_types
                or urls
            )
        ):
            level = "danger"
        elif score >= 0.65:
            level = "danger"
        elif score >= 0.30:
            level = "warning"
        else:
            level = "safe"

        if level == "safe":

            reasons = [
                "Email appears relatively legitimate",
                "No major phishing indicators detected"
            ]

            confidence = max(
                0.75,
                min(0.95, 1.0 - score)
            )

        else:

            confidence = min(
                0.99,
                max(
                    0.60,
                    0.50 + score
                )
            )

        return {
            "sender": sender,
            "threat_level": level,
            "confidence": round(
                confidence,
                2
            ),
            "threat_type": (
                threat_types[0]
                if threat_types
                else "None"
            ),
            "threat_types": list(
                dict.fromkeys(threat_types)
            ),
            "reasons": reasons,
            "links_found": len(urls),
            "recommendation": self._get_recommendation(
                level,
                threat_types
            ),
            "model": "ML + NLP Pattern Analysis",
            "score": round(score, 2),
        }

    # ============================================================
    # RECOMMENDATIONS
    # ============================================================

    def _get_recommendation(
        self,
        level: str,
        threat_types: list
    ) -> str:

        if level == "danger":

            return (
                "Do NOT respond, pay money, share OTP/passwords, "
                "or click links. Verify through the official "
                "organization website or app."
            )

        elif level == "warning":

            if "Job Scam" in threat_types:

                return (
                    "Do not pay any registration, security, "
                    "training, or activation fee for a job. "
                    "Verify the employer through official channels."
                )

            if "Refund Scam" in threat_types:

                return (
                    "Do not provide bank details, OTPs, or pay "
                    "fees to receive a refund. Contact the "
                    "merchant through its official website or app."
                )

            return (
                "Verify the sender through official channels. "
                "Do not share personal information, OTPs, "
                "passwords, or payment details."
            )

        return (
            "No major scam indicators detected. "
            "Still stay vigilant with unknown senders."
        )

    # ============================================================
    # ERROR RESULT
    # ============================================================

    def _error_result(
        self,
        message: str
    ) -> dict:

        return {
            "threat_level": "unknown",
            "confidence": 0,
            "threat_type": "Error",
            "reasons": [message],
            "recommendation": "Please provide valid content",
            "error": message
        }