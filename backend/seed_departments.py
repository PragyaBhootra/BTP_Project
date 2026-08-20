"""Run once locally to seed dummy department emails for testing.

Usage:
    python seed_departments.py
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

DEPARTMENTS = [
    {"department": "railway", "label": "Railway", "email": "pbhootra2005@gmail.com"},
    {"department": "delhi_police", "label": "Delhi Police", "email": "pragyabhootra246@gmail.com"},
    {"department": "income_tax", "label": "Income Tax", "email": "pbhootra2005@gmail.com"},
    {"department": "delhi_traffic", "label": "Delhi Traffic Police", "email": "pragyabhootra246@gmail.com"},
    {"department": "general", "label": "General Grievance", "email": "pbhootra2005@gmail.com"},
]

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["complaintdb"]

for dept in DEPARTMENTS:
    db.departments.update_one(
        {"department": dept["department"]}, {"$set": dept}, upsert=True
    )
    print(f"Upserted: {dept['department']} -> {dept['email']}")

print("Done.")
