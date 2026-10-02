"""News model operations."""
from datetime import datetime
from typing import Optional

from bson import ObjectId

from utils.database import get_collection, normalize_object_id, serialize_doc, paginate


class NewsModel:
    """MongoDB operations for cyber news."""

    COLLECTION = "news"

    @classmethod
    def _col(cls):
        return get_collection(cls.COLLECTION)

    @classmethod
    def create(cls, data: dict) -> dict:
        """Create news article."""
        data["created_at"] = datetime.utcnow()
        data.setdefault("bookmarks", [])
        data.setdefault("views", 0)
        result = cls._col().insert_one(data)
        data["_id"] = result.inserted_id
        return serialize_doc(data)

    @classmethod
    def find_all(cls, category: str = None, search: str = None,
                 page: int = 1, per_page: int = 12) -> dict:
        """Get news with filters."""
        query = {}
        if category:
            query["category"] = category
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"summary": {"$regex": search, "$options": "i"}},
                {"content": {"$regex": search, "$options": "i"}}
            ]
        return paginate(cls._col(), query, page, per_page)

    @classmethod
    def find_by_id(cls, news_id: str) -> Optional[dict]:
        """Find news by ID."""
        normalized_id = normalize_object_id(news_id)
        doc = cls._col().find_one({"_id": normalized_id})
        if doc:
            cls._col().update_one({"_id": normalized_id}, {"$inc": {"views": 1}})
        return serialize_doc(doc)

    @classmethod
    def update(cls, news_id: str, data: dict) -> bool:
        """Update news article."""
        data["updated_at"] = datetime.utcnow()
        result = cls._col().update_one({"_id": normalize_object_id(news_id)}, {"$set": data})
        return result.modified_count > 0

    @classmethod
    def delete(cls, news_id: str) -> bool:
        """Delete news article."""
        result = cls._col().delete_one({"_id": normalize_object_id(news_id)})
        return result.deleted_count > 0

    @classmethod
    def toggle_bookmark(cls, news_id: str, user_id: str) -> bool:
        """Toggle bookmark for user."""
        normalized_id = normalize_object_id(news_id)
        doc = cls._col().find_one({"_id": normalized_id})
        if not doc:
            return False
        bookmarks = doc.get("bookmarks", [])
        if user_id in bookmarks:
            bookmarks.remove(user_id)
        else:
            bookmarks.append(user_id)
        cls._col().update_one({"_id": normalized_id}, {"$set": {"bookmarks": bookmarks}})
        return user_id in bookmarks
