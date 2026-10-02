"""URL feature extraction for ML-based phishing detection."""
import re
from urllib.parse import urlparse


SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq", "xyz", "top", "work", "click", "loan",
    "win", "bid", "stream", "download", "racing", "party", "review"
}

SUSPICIOUS_KEYWORDS = {
    "login", "verify", "secure", "account", "update", "confirm", "banking",
    "password", "wallet", "paypal", "signin", "credential", "suspend",
    "unlock", "restore", "validate", "authenticate", "otp", "kyc"
}

SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd", "buff.ly"
}


def extract_url_features(url: str) -> list[float]:
    """Extract numerical features from URL for Random Forest model."""
    url = url.strip().lower()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        parsed = urlparse("https://unknown.com")

    hostname = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""

    # Feature vector (20 features)
    features = [
        len(url),                                          # 0: URL length
        url.count("."),                                    # 1: Dot count
        url.count("-"),                                    # 2: Hyphen count
        url.count("@"),                                    # 3: At symbol count
        url.count("//"),                                   # 4: Double slash count
        1 if parsed.scheme == "https" else 0,              # 5: Uses HTTPS
        1 if re.search(r"\d", hostname) else 0,             # 6: IP or digits in hostname
        1 if hostname.replace(".", "").isdigit() else 0,   # 7: Is IP address
        len(hostname),                                     # 8: Hostname length
        len(path),                                         # 9: Path length
        len(query),                                        # 10: Query length
        path.count("/"),                                   # 11: Path depth
        1 if any(tld in hostname for tld in SUSPICIOUS_TLDS) else 0,  # 12: Suspicious TLD
        sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in url), # 13: Suspicious keywords
        1 if any(sd in hostname for sd in SHORTENER_DOMAINS) else 0,  # 14: URL shortener
        1 if url.count("https") > 1 or url.count("http") > 1 else 0,  # 15: Redirect chain
        1 if "%" in url else 0,                            # 16: URL encoding
        1 if len(hostname.split(".")) > 4 else 0,          # 17: Subdomain count
        1 if re.search(r"[A-Z]", url) else 0,              # 18: Mixed case (suspicious)
        1 if "@" in url else 0,                            # 19: Credential in URL
    ]
    return [float(f) for f in features]


def heuristic_url_score(url: str) -> tuple[str, float, list[str]]:
    """Rule-based URL threat scoring fallback."""
    url_lower = url.strip().lower()
    if not url_lower.startswith(("http://", "https://")):
        url_lower = "https://" + url_lower

    score = 0.0
    reasons = []

    try:
        parsed = urlparse(url_lower)
        hostname = parsed.hostname or ""
    except Exception:
        return "danger", 0.92, ["Malformed or unparseable URL"]

    # HTTPS check
    if parsed.scheme != "https":
        score += 0.15
        reasons.append("URL does not use HTTPS encryption")

    # Suspicious TLD
    for tld in SUSPICIOUS_TLDS:
        if hostname.endswith("." + tld) or hostname.endswith(tld):
            score += 0.25
            reasons.append(f"Suspicious top-level domain (.{tld})")
            break

    # IP address
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname):
        score += 0.30
        reasons.append("URL uses IP address instead of domain name")

    # Suspicious keywords
    keyword_hits = [kw for kw in SUSPICIOUS_KEYWORDS if kw in url_lower]
    if keyword_hits:
        score += min(0.20, len(keyword_hits) * 0.05)
        reasons.append(f"Contains suspicious keywords: {', '.join(keyword_hits[:3])}")

    # URL shortener
    for sd in SHORTENER_DOMAINS:
        if sd in hostname:
            score += 0.20
            reasons.append("URL uses a link shortener service")
            break

    # Excessive length
    if len(url_lower) > 100:
        score += 0.10
        reasons.append("Unusually long URL")

    # Subdomain count
    if hostname.count(".") > 3:
        score += 0.15
        reasons.append("Excessive subdomains detected")

    # @ symbol
    if "@" in url_lower:
        score += 0.25
        reasons.append("URL contains @ symbol (credential phishing)")

    confidence = min(0.99, max(0.55, score + 0.5))

    if score >= 0.5:
        level = "danger"
    elif score >= 0.25:
        level = "warning"
    else:
        level = "safe"
        reasons = ["URL appears legitimate", "No major red flags detected"]
        confidence = max(0.75, 1.0 - score)

    return level, round(confidence, 2), reasons
