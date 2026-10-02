"""Threat report model operations."""
from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId

from utils.database import get_collection, normalize_object_id, serialize_doc, paginate


class ThreatReportModel:
    """MongoDB operations for threat reports."""

    COLLECTION = "threat_reports"

    @classmethod
    def _col(cls):
        return get_collection(cls.COLLECTION)

    @classmethod
    def create(cls, data: dict) -> dict:
        """Create threat report."""
        data["created_at"] = datetime.utcnow()
        result = cls._col().insert_one(data)
        data["_id"] = result.inserted_id
        return serialize_doc(data)

    @classmethod
    def find_by_user(cls, user_id: str, page: int = 1, per_page: int = 20) -> dict:
        """Get reports for user."""
        return paginate(cls._col(), {"user_id": user_id}, page, per_page)

    @classmethod
    def find_by_id(cls, report_id: str) -> Optional[dict]:
        """Find report by ID."""
        doc = cls._col().find_one({"_id": normalize_object_id(report_id)})
        return serialize_doc(doc)

    @classmethod
    def get_stats(cls, user_id: str = None) -> dict:
        """Get threat statistics."""
        query = {"user_id": user_id} if user_id else {}
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        total = cls._col().count_documents(query)
        today = cls._col().count_documents({**query, "created_at": {"$gte": today_start}})
        week = cls._col().count_documents({**query, "created_at": {"$gte": week_start}})
        month = cls._col().count_documents({**query, "created_at": {"$gte": month_start}})

        # Threat level distribution
        pipeline = [
            {"$match": query},
            {"$group": {"_id": "$threat_level", "count": {"$sum": 1}}}
        ]
        distribution = {item["_id"]: item["count"] for item in cls._col().aggregate(pipeline)}

        # Threat type distribution
        type_pipeline = [
            {"$match": query},
            {"$group": {"_id": "$threat_type", "count": {"$sum": 1}}}
        ]
        type_dist = {item["_id"]: item["count"] for item in cls._col().aggregate(type_pipeline)}

        # Recent activity (last 7 days daily)
        daily = []
        for i in range(6, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            count = cls._col().count_documents({
                **query,
                "created_at": {"$gte": day_start, "$lt": day_end}
            })
            daily.append({"date": day_start.strftime("%Y-%m-%d"), "count": count})

        return {
            "total_scans": total,
            "today_scans": today,
            "weekly_scans": week,
            "monthly_scans": month,
            "threat_distribution": distribution,
            "threat_type_distribution": type_dist,
            "daily_scans": daily,
            "threats_blocked": sum(
                c for level, c in distribution.items() if level in ("danger", "warning")
            )
        }

    @classmethod
    def get_recent(cls, user_id: str = None, limit: int = 10) -> list:
        """Get recent reports."""
        query = {"user_id": user_id} if user_id else {}
        cursor = cls._col().find(query).sort("created_at", -1).limit(limit)
        return [serialize_doc(doc) for doc in cursor]

    @classmethod
    def count_all(cls) -> int:
        """Count all reports."""
        return cls._col().count_documents({})
