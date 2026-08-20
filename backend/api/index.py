import os
import sys

# allow `utils` to be imported when Vercel builds this as api/index.py
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from utils.slot_filling import extract_slots, build_reply
from utils.classify import classify_department
from utils.db import get_department_email, list_departments
from utils.email_sender import send_complaint_email
from utils.advice import generate_user_advice, generate_authority_advice

load_dotenv(override=True)

app = Flask(__name__)
CORS(app)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/auth/google", methods=["POST"])
def auth_google():
    """Verify the Google ID token sent by the frontend after login."""
    token = request.json.get("credential", "")
    try:
        info = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
        return jsonify({
            "email": info.get("email"),
            "name": info.get("name"),
            "picture": info.get("picture"),
        })
    except ValueError as e:
        return jsonify({"error": f"Invalid token: {e}"}), 401


@app.route("/api/chat", methods=["POST"])
def chat():
    """Stateless slot-filling turn. The frontend sends the whole
    complaint_data it has so far; we never rely on server memory,
    since serverless instances aren't guaranteed to persist between calls.
    """
    data = request.json or {}
    message = data.get("message", "")
    complaint_data = data.get("complaint_data", {})

    updated = extract_slots(message, complaint_data)
    reply, is_complete = build_reply(updated)

    return jsonify({
        "reply": reply,
        "complaint_data": updated,
        "is_complete": is_complete,
    })


@app.route("/api/classify", methods=["POST"])
def classify():
    data = request.json or {}
    complaint_data = data.get("complaint_data", {})
    complaint_text = complaint_data.get("description", "")

    departments = list_departments() or [
        "railway", "delhi_police", "income_tax", "delhi_traffic", "general"
    ]
    department, confidence = classify_department(complaint_text, departments)

    return jsonify({"department": department, "confidence": confidence})


@app.route("/api/send-complaint", methods=["POST"])
def send_complaint():
    data = request.json or {}
    department = data.get("department", "general")
    complaint_data = data.get("complaint_data", {})
    user_email = data.get("user_email", "")

    to_email = get_department_email(department)
    user_advice = generate_user_advice(complaint_data, department)
    authority_advice = generate_authority_advice(complaint_data, department)

    success = send_complaint_email(to_email, department, complaint_data, user_email, authority_advice)

    if success:
        return jsonify({
            "success": True,
            "department": department,
            "sent_to": to_email,
            "advice": user_advice,
        })
    return jsonify({"success": False, "message": "Failed to send email"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
