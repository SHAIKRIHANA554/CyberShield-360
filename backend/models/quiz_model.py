"""Quiz model operations."""
from datetime import datetime
from typing import Optional

from bson import ObjectId

from utils.database import get_collection, normalize_object_id, serialize_doc, paginate


class QuizModel:
    """MongoDB operations for quizzes."""

    COLLECTION = "quiz"

    @classmethod
    def _col(cls):
        return get_collection(cls.COLLECTION)

    @classmethod
    def create(cls, data: dict) -> dict:
        """Create quiz."""
        data["created_at"] = datetime.utcnow()
        result = cls._col().insert_one(data)
        data["_id"] = result.inserted_id
        return serialize_doc(data)

    @classmethod
    def find_all(cls, page: int = 1, per_page: int = 20) -> dict:
        """Get all quizzes."""
        return paginate(cls._col(), {"is_active": True}, page, per_page)

    @classmethod
    def find_by_id(cls, quiz_id: str) -> Optional[dict]:
        """Find quiz by ID."""
        doc = cls._col().find_one({"_id": normalize_object_id(quiz_id)})
        if doc:
            # Don't expose correct answers in list view
            return serialize_doc(doc)
        return None

    @classmethod
    def submit_result(cls, user_id: str, quiz_id: str, score: int,
                      total: int, answers: list, time_taken: int) -> dict:
        """Submit quiz result."""
        percentage = round((score / total) * 100, 2) if total > 0 else 0
        data = {
            "user_id": user_id,
            "quiz_id": quiz_id,
            "score": score,
            "total": total,
            "percentage": percentage,
            "answers": answers,
            "time_taken": time_taken,
            "created_at": datetime.utcnow()
        }
        result = get_collection("quiz_results").insert_one(data)
        data["_id"] = result.inserted_id

        # Award certificate if score >= 80%
        if percentage >= 80:
            get_collection("certificates").insert_one({
                "user_id": user_id,
                "quiz_id": quiz_id,
                "score": percentage,
                "issued_at": datetime.utcnow()
            })

        return serialize_doc(data)

    @classmethod
    def get_leaderboard(cls, quiz_id: str = None, limit: int = 10) -> list:
        """Get quiz leaderboard."""
        match = {"quiz_id": quiz_id} if quiz_id else {}
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": "$user_id",
                "best_score": {"$max": "$percentage"},
                "attempts": {"$sum": 1}
            }},
            {"$sort": {"best_score": -1}},
            {"$limit": limit}
        ]
        results = list(get_collection("quiz_results").aggregate(pipeline))

        # Enrich with user names
        for r in results:
            user = get_collection("users").find_one({"_id": normalize_object_id(r["_id"])})
            r["user_name"] = user.get("name", "Anonymous") if user else "Anonymous"
            r["user_id"] = str(r["_id"])
            del r["_id"]

        return results

    @classmethod
    def get_user_results(cls, user_id: str) -> list:
        """Get quiz results for user."""
        cursor = get_collection("quiz_results").find({"user_id": user_id}).sort("created_at", -1)
        return [serialize_doc(doc) for doc in cursor]

    @classmethod
    def update(cls, quiz_id: str, data: dict) -> bool:
        """Update quiz."""
        result = cls._col().update_one({"_id": normalize_object_id(quiz_id)}, {"$set": data})
        return result.modified_count > 0

    @classmethod
    def delete(cls, quiz_id: str) -> bool:
        """Delete quiz."""
        result = cls._col().delete_one({"_id": normalize_object_id(quiz_id)})
        return result.deleted_count > 0
