"""Input validation utilities."""
import re
from urllib.parse import urlparse
from werkzeug.utils import secure_filename

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
URL_REGEX = re.compile(
    r"^(https?://)?([\w\-]+\.)+[\w\-]+(/[\w\-._~:/?#\[\]@!$&'()*+,;=%]*)?$",
    re.IGNORECASE
)
PHONE_REGEX = re.compile(r"^\+?[\d\s\-()]{10,15}$")


def validate_email(email: str) -> bool:
    """Validate email format."""
    return bool(email and EMAIL_REGEX.match(email.strip()))


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    return True, "Valid"


def validate_url(url: str) -> bool:
    """Validate URL format."""
    if not url:
        return False
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return bool(URL_REGEX.match(url))


def normalize_url(url: str) -> str:
    """Normalize URL with scheme."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text."""
    pattern = re.compile(
        r"https?://[\w\-._~:/?#\[\]@!$&'()*+,;=%]+|"
        r"www\.[\w\-._~:/?#\[\]@!$&'()*+,;=%]+|"
        r"[\w\-]+\.(?:com|net|org|in|co|io|xyz|info|biz|me|app|dev|tech|online|site|store|shop|click|top|work|live|pro|cc|tk|ml|ga|cf|gq)(?:/[\w\-._~:/?#\[\]@!$&'()*+,;=%]*)?",
        re.IGNORECASE
    )
    return list(set(m.group(0) for m in pattern.finditer(text)))


def extract_emails(text: str) -> list[str]:
    """Extract email addresses from text."""
    return list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)))


def extract_phones(text: str) -> list[str]:
    """Extract phone numbers from text."""
    return list(set(re.findall(r"\+?\d[\d\s\-()]{8,14}\d", text)))


def extract_upi_ids(text: str) -> list[str]:
    """Extract UPI IDs from text."""
    return list(set(re.findall(r"[\w.\-]+@[\w]+", text)))


def allowed_file(filename: str, allowed: set) -> bool:
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def secure_file(filename: str) -> str:
    """Get secure filename."""
    return secure_filename(filename)


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input."""
    if not text:
        return ""
    text = text.strip()[:max_length]
    return text
