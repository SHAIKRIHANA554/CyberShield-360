"""Learning content model."""
from datetime import datetime
from typing import Optional

from bson import ObjectId

from utils.database import get_collection, normalize_object_id, serialize_doc, paginate


class LearningModel:
    """MongoDB operations for learning modules."""

    COLLECTION = "learning"

    @classmethod
    def _col(cls):
        return get_collection(cls.COLLECTION)

    @classmethod
    def create(cls, data: dict) -> dict:
        """Create learning module."""
        data["created_at"] = datetime.utcnow()
        result = cls._col().insert_one(data)
        data["_id"] = result.inserted_id
        return serialize_doc(data)

    @classmethod
    def find_all(cls, category: str = None, page: int = 1, per_page: int = 20) -> dict:
        """Get learning modules."""
        query = {"is_active": True} if category is None else {"category": category, "is_active": True}
        if category:
            query["category"] = category
        return paginate(cls._col(), query, page, per_page)

    @classmethod
    def find_by_id(cls, module_id: str) -> Optional[dict]:
        """Find module by ID."""
        return serialize_doc(cls._col().find_one({"_id": normalize_object_id(module_id)}))

    @classmethod
    def update(cls, module_id: str, data: dict) -> bool:
        """Update learning module."""
        result = cls._col().update_one({"_id": normalize_object_id(module_id)}, {"$set": data})
        return result.modified_count > 0

    @classmethod
    def delete(cls, module_id: str) -> bool:
        """Delete learning module."""
        result = cls._col().delete_one({"_id": normalize_object_id(module_id)})
        return result.deleted_count > 0

    @classmethod
    def update_progress(cls, user_id: str, module_id: str, progress: int) -> None:
        """Update user learning progress."""
        get_collection("learning_progress").update_one(
            {"user_id": user_id, "module_id": module_id},
            {"$set": {"progress": progress, "updated_at": datetime.utcnow()},
             "$setOnInsert": {"created_at": datetime.utcnow()}},
            upsert=True
        )

    @classmethod
    def get_user_progress(cls, user_id: str) -> list:
        """Get all progress for user."""
        cursor = get_collection("learning_progress").find({"user_id": user_id})
        return [serialize_doc(doc) for doc in cursor]
