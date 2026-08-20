"""Generates plain-language advice using Gemini -- once per submission,
for both the complainant and the receiving department. Uses the current
Google Gen AI SDK (the older google.generativeai package is deprecated).
"""
import os
from dotenv import load_dotenv
from google import genai

_client = None

load_dotenv(override=True)

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def generate_user_advice(complaint_data: dict, department: str) -> str:
    """Advice shown back to the person who filed the complaint."""
    prompt = f"""
A user filed this complaint, routed to the {department.replace('_', ' ').title()} department:

What happened: {complaint_data.get('description', 'Not provided')}
Location: {complaint_data.get('location', 'Not provided')}
When: {complaint_data.get('time', 'Not provided')}

In 3-4 short bullet points, tell the user:
- what to expect next (rough response time/process)
- any evidence they should preserve
- one practical next step they can take themselves

Keep it plain, empathetic, and brief. No headers, just bullet points.
"""
    try:
        client = _get_client()
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except Exception as e:
        print(f"User advice generation failed: {e}")
        return "Your complaint has been submitted. The department will review it and reach out if follow-up is needed."


def generate_authority_advice(complaint_data: dict, department: str) -> str:
    """Recommended action, included in the email sent to the department."""
    prompt = f"""
A citizen complaint was routed to the {department.replace('_', ' ').title()} department:

What happened: {complaint_data.get('description', 'Not provided')}
Location: {complaint_data.get('location', 'Not provided')}
When: {complaint_data.get('time', 'Not provided')}

In 3-4 short bullet points, recommend:
- the immediate action this department should take
- a rough priority level (Low/Medium/High)
- any relevant jurisdiction or process note

Keep it concise and professional. No headers, just bullet points.
"""
    try:
        client = _get_client()
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Authority advice generation failed: {e}")
        return "Please review and action this complaint per standard procedure."