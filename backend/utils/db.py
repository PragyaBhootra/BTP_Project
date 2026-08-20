"""MongoDB access — department -> email lookup."""
import os
import certifi
from pymongo import MongoClient

_client = None


def get_db():
    global _client
    if _client is None:
        _client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=certifi.where())
    return _client["complaintdb"]


def get_department_email(department: str) -> str:
    db = get_db()
    doc = db.departments.find_one({"department": department})
    if not doc:
        doc = db.departments.find_one({"department": "general"})
    return doc["email"] if doc else "general@example.com"


def list_departments() -> list:
    db = get_db()
    return [d["department"] for d in db.departments.find({}, {"department": 1})]
