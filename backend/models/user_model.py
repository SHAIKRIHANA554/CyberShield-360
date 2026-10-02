"""User model operations."""
from datetime import datetime
from typing import Optional

from bson import ObjectId

from utils.database import get_collection, normalize_object_id, serialize_doc


class UserModel:
    """MongoDB operations for users collection."""

    COLLECTION = "users"

    @classmethod
    def _col(cls):
        return get_collection(cls.COLLECTION)

    @classmethod
    def create(cls, data: dict) -> dict:
        """Create new user."""
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        data.setdefault("role", "user")
        data.setdefault("awareness_score", 0)
        data.setdefault("badges", [])
        data.setdefault("achievements", [])
        data.setdefault("is_verified", False)
        data.setdefault("is_active", True)
        result = cls._col().insert_one(data)
        data["_id"] = result.inserted_id
        return serialize_doc(data)

    @classmethod
    def find_by_email(cls, email: str) -> Optional[dict]:
        """Find user by email."""
        return cls._col().find_one({"email": email.lower().strip()})

    @classmethod
    def find_by_id(cls, user_id: str) -> Optional[dict]:
        """Find user by ID."""
        return cls._col().find_one({"_id": normalize_object_id(user_id)})

    @classmethod
    def update(cls, user_id: str, data: dict) -> bool:
        """Update user."""
        data["updated_at"] = datetime.utcnow()
        result = cls._col().update_one({"_id": normalize_object_id(user_id)}, {"$set": data})
        return result.modified_count > 0

    @classmethod
    def update_otp(cls, email: str, otp: str, expiry: datetime) -> bool:
        """Store OTP for password reset."""
        result = cls._col().update_one(
            {"email": email.lower().strip()},
            {"$set": {"reset_otp": otp, "reset_otp_expiry": expiry, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    @classmethod
    def verify_otp(cls, email: str, otp: str) -> bool:
        """Verify OTP."""
        user = cls.find_by_email(email)
        if not user:
            return False
        if user.get("reset_otp") != otp:
            return False
        expiry = user.get("reset_otp_expiry")
        if expiry and expiry < datetime.utcnow():
            return False
        return True

    @classmethod
    def clear_otp(cls, email: str) -> None:
        """Clear OTP after verification."""
        cls._col().update_one(
            {"email": email.lower().strip()},
            {"$unset": {"reset_otp": "", "reset_otp_expiry": ""}}
        )

    @classmethod
    def get_all(cls, page: int = 1, per_page: int = 20) -> list:
        """Get all users for admin."""
        skip = (page - 1) * per_page
        users = cls._col().find().sort("created_at", -1).skip(skip).limit(per_page)
        return [serialize_doc(u) for u in users]

    @classmethod
    def count(cls) -> int:
        """Count total users."""
        return cls._col().count_documents({})

    @classmethod
    def delete(cls, user_id: str) -> bool:
        """Delete user."""
        result = cls._col().delete_one({"_id": normalize_object_id(user_id)})
        return result.deleted_count > 0
