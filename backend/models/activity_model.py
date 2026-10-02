"""Activity log model."""
from datetime import datetime

from utils.database import get_collection, serialize_doc, paginate


class ActivityLogModel:
    """MongoDB operations for activity logs."""

    COLLECTION = "activity_logs"

    @classmethod
    def _col(cls):
        return get_collection(cls.COLLECTION)

    @classmethod
    def log(cls, user_id: str, action: str, details: str = "", module: str = "") -> dict:
        """Create activity log entry."""
        data = {
            "user_id": user_id,
            "action": action,
            "details": details,
            "module": module,
            "created_at": datetime.utcnow()
        }
        result = cls._col().insert_one(data)
        data["_id"] = result.inserted_id
        return serialize_doc(data)

    @classmethod
    def get_by_user(cls, user_id: str, page: int = 1, per_page: int = 20) -> dict:
        """Get activity logs for user."""
        return paginate(cls._col(), {"user_id": user_id}, page, per_page)

    @classmethod
    def get_recent(cls, user_id: str = None, limit: int = 10) -> list:
        """Get recent activities."""
        query = {"user_id": user_id} if user_id else {}
        cursor = cls._col().find(query).sort("created_at", -1).limit(limit)
        return [serialize_doc(doc) for doc in cursor]
