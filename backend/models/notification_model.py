"""Notification model operations."""
from datetime import datetime
from typing import Optional

from bson import ObjectId

from utils.database import get_collection, normalize_object_id, serialize_doc, paginate


class NotificationModel:
    """MongoDB operations for notifications."""

    COLLECTION = "notifications"

    @classmethod
    def _col(cls):
        return get_collection(cls.COLLECTION)

    @classmethod
    def create(cls, data: dict) -> dict:
        """Create notification."""
        data["created_at"] = datetime.utcnow()
        data.setdefault("is_read", False)
        result = cls._col().insert_one(data)
        data["_id"] = result.inserted_id
        return serialize_doc(data)

    @classmethod
    def get_for_user(cls, user_id: str = None, page: int = 1, per_page: int = 20) -> dict:
        """Get notifications - global or user-specific."""
        query = {"$or": [{"user_id": user_id}, {"user_id": None}, {"is_global": True}]}
        if user_id is None:
            query = {"is_global": True}
        return paginate(cls._col(), query, page, per_page)

    @classmethod
    def get_unread_count(cls, user_id: str) -> int:
        """Get unread notification count."""
        return cls._col().count_documents({
            "$or": [{"user_id": user_id}, {"is_global": True}],
            "is_read": False
        })

    @classmethod
    def mark_read(cls, notification_id: str) -> bool:
        """Mark notification as read."""
        result = cls._col().update_one(
            {"_id": normalize_object_id(notification_id)},
            {"$set": {"is_read": True}}
        )
        return result.modified_count > 0

    @classmethod
    def mark_all_read(cls, user_id: str) -> int:
        """Mark all notifications as read for user."""
        result = cls._col().update_many(
            {"$or": [{"user_id": user_id}, {"is_global": True}], "is_read": False},
            {"$set": {"is_read": True}}
        )
        return result.modified_count

    @classmethod
    def delete(cls, notification_id: str) -> bool:
        """Delete notification."""
        result = cls._col().delete_one({"_id": normalize_object_id(notification_id)})
        return result.deleted_count > 0
