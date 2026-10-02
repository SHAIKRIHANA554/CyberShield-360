"""Security utilities - password hashing, OTP generation."""
import random
import string
from datetime import datetime, timedelta

import bcrypt


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def generate_otp(length: int = 6) -> str:
    """Generate numeric OTP."""
    return "".join(random.choices(string.digits, k=length))


def otp_expiry(minutes: int = 10) -> datetime:
    """Get OTP expiry datetime."""
    return datetime.utcnow() + timedelta(minutes=minutes)
