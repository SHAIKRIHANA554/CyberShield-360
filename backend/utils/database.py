"""MongoDB database connection and helpers."""
import copy
import re
import uuid
from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

_client: Optional[MongoClient] = None
_db: Optional[Database] = None
_memory_collections: dict[str, Any] = {}


def normalize_object_id(value: Any) -> Any:
    """Coerce valid Mongo ObjectId strings while preserving in-memory UUID strings."""
    if value is None:
        return None
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return candidate
        try:
            if len(candidate) == 24 and all(ch in "0123456789abcdefABCDEF" for ch in candidate):
                return ObjectId(candidate)
        except Exception:
            pass
    return value


class MemoryCursor:
    """Simple cursor implementation for the in-memory fallback store."""

    def __init__(self, docs: list[dict]):
        self.docs = docs

    def sort(self, field: str, order: int = -1):
        def _sort_key(doc: dict):
            value = doc.get(field)
            if isinstance(value, datetime):
                return value
            if value is None:
                return ""
            return str(value).lower() if isinstance(value, str) else value

        self.docs = sorted(self.docs, key=_sort_key, reverse=order < 0)
        return self

    def skip(self, count: int):
        self.docs = self.docs[count:] if count < len(self.docs) else []
        return self

    def limit(self, count: int):
        self.docs = self.docs[:count]
        return self

    def __iter__(self):
        return iter(self.docs)


class MemoryCollection:
    """Minimal in-memory collection supporting common CRUD operations."""

    def __init__(self):
        self.docs: list[dict] = []

    def _normalize_id(self, value: Any) -> Any:
        if isinstance(value, ObjectId):
            return str(value)
        return value

    def _match_value(self, doc_value: Any, query_value: Any) -> bool:
        if isinstance(query_value, dict):
            for op, expected in query_value.items():
                if op == "$gte" and not (doc_value >= expected):
                    return False
                if op == "$gt" and not (doc_value > expected):
                    return False
                if op == "$lte" and not (doc_value <= expected):
                    return False
                if op == "$lt" and not (doc_value < expected):
                    return False
                if op == "$ne" and doc_value == expected:
                    return False
                if op == "$in" and doc_value not in expected:
                    return False
                if op == "$regex" and not re.search(expected, str(doc_value), re.IGNORECASE):
                    return False
            return True

        if isinstance(query_value, str) and isinstance(doc_value, str):
            return doc_value.lower() == query_value.lower()
        return self._normalize_id(doc_value) == self._normalize_id(query_value)

    def _match_query(self, doc: dict, query: dict) -> bool:
        if not query:
            return True
        for key, value in query.items():
            if key == "$or":
                if not any(self._match_query(doc, clause) for clause in value):
                    return False
                continue
            if key == "$and":
                if not all(self._match_query(doc, clause) for clause in value):
                    return False
                continue
            if key not in doc:
                return False
            if not self._match_value(doc[key], value):
                return False
        return True

    def insert_one(self, data: dict):
        doc = copy.deepcopy(data)
        if "_id" not in doc:
            doc["_id"] = str(uuid.uuid4())
        self.docs.append(doc)
        return type("Result", (), {"inserted_id": doc["_id"]})()

    def find_one(self, query: dict):
        for doc in self.docs:
            if self._match_query(doc, query):
                return copy.deepcopy(doc)
        return None

    def find(self, query: dict = None):
        q = query or {}
        docs = [copy.deepcopy(doc) for doc in self.docs if self._match_query(doc, q)]
        return MemoryCursor(docs)

    def update_one(self, query: dict, update: dict, upsert: bool = False):
        for doc in self.docs:
            if not self._match_query(doc, query):
                continue
            for key, value in update.get("$set", {}).items():
                doc[key] = value
            for key in update.get("$unset", {}):
                doc.pop(key, None)
            for key, value in update.get("$inc", {}).items():
                doc[key] = doc.get(key, 0) + value
            return type("Result", (), {"modified_count": 1})()
        if upsert:
            doc = {key: value for key, value in query.items() if not key.startswith("$")}
            doc.update(update.get("$setOnInsert", {}))
            doc.update(update.get("$set", {}))
            for key, value in update.get("$inc", {}).items():
                doc[key] = doc.get(key, 0) + value
            self.insert_one(doc)
            return type("Result", (), {"modified_count": 1})()
        return type("Result", (), {"modified_count": 0})()

    def update_many(self, query: dict, update: dict):
        modified = 0
        for doc in self.docs:
            if not self._match_query(doc, query):
                continue
            for key, value in update.get("$set", {}).items():
                doc[key] = value
            for key in update.get("$unset", {}):
                doc.pop(key, None)
            modified += 1
        return type("Result", (), {"modified_count": modified})()

    def delete_one(self, query: dict):
        for idx, doc in enumerate(self.docs):
            if self._match_query(doc, query):
                del self.docs[idx]
                return type("Result", (), {"deleted_count": 1})()
        return type("Result", (), {"deleted_count": 0})()

    def count_documents(self, query: dict):
        return len([doc for doc in self.docs if self._match_query(doc, query)])

    def aggregate(self, pipeline: list[dict]):
        docs = list(self.docs)
        for stage in pipeline:
            if "$match" in stage:
                docs = [doc for doc in docs if self._match_query(doc, stage["$match"])]
            elif "$group" in stage:
                grouped = {}
                for doc in docs:
                    key = doc.get(stage["$group"].get("_id"), "")
                    if isinstance(key, str) and key.startswith("$"):
                        key = doc.get(key[1:], "")
                    grouped.setdefault(key, {"count": 0})
                    grouped[key]["count"] += 1
                return [{"_id": key, "count": values["count"]} for key, values in grouped.items()]
        return []


def init_db(uri: str, db_name: str):
    """Initialize MongoDB connection with an in-memory fallback."""
    global _client, _db, _memory_collections
    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=8000)
        _client.admin.command('ping')
        _db = _client[db_name]
        print(f"Connected to MongoDB database: {db_name}")
    except Exception as e:
        print(f"MongoDB connection ping failed ({e}). Using in-memory database fallback.")
        _client = None
        _db = None
        _memory_collections.clear()
    return _db


def get_db():
    """Get database instance."""
    if _db is None:
        return None
    return _db


def get_collection(name: str):
    """Get a MongoDB collection by name. Falls back to an in-memory collection."""
    if _db is None:
        if name not in _memory_collections:
            _memory_collections[name] = MemoryCollection()
        return _memory_collections[name]
    return get_db()[name]


def serialize_doc(doc: Optional[dict]) -> Optional[dict]:
    """Convert MongoDB document to JSON-serializable dict."""
    if doc is None:
        return None
    result = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, list):
            result[key] = [
                serialize_doc(v) if isinstance(v, dict) else
                str(v) if isinstance(v, ObjectId) else v
                for v in value
            ]
        elif isinstance(value, dict):
            result[key] = serialize_doc(value)
        else:
            result[key] = value
    return result


def to_object_id(id_str: str) -> ObjectId:
    """Convert string to ObjectId."""
    return ObjectId(id_str)


def paginate(collection: Collection, query: dict, page: int = 1,
             per_page: int = 20, sort_field: str = "created_at",
             sort_order: int = -1) -> dict:
    """Paginate query results."""
    skip = (page - 1) * per_page
    total = collection.count_documents(query)
    cursor = collection.find(query).sort(sort_field, sort_order).skip(skip).limit(per_page)
    items = [serialize_doc(doc) for doc in cursor]
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, (total + per_page - 1) // per_page)
    }
