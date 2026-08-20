"""Sends the final complaint to the department's email over SMTP, from the
existing 'safety bot' mail account.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def format_email_body(complaint_data: dict, department: str, user_email: str, authority_advice: str = "") -> str:
    return f"""New Complaint - {department.replace('_', ' ').title()}

Submitted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Complainant: {user_email}

What happened:
{complaint_data.get('description', 'Not provided')}

Location:
{complaint_data.get('location', 'Not provided')}

When:
{complaint_data.get('time', 'Not provided')}

Contact:
{complaint_data.get('contact', 'Not provided')}

---
Recommended action:
{authority_advice}

---
Automatically routed by the Complaint Classification System.
"""


def send_complaint_email(to_email: str, department: str, complaint_data: dict, user_email: str, authority_advice: str = "") -> bool:
    sender_email = os.getenv("GMAIL_USER")
    sender_password = os.getenv("GMAIL_APP_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = f"New Complaint - {department.replace('_', ' ').title()}"
    if user_email:
        message["Cc"] = user_email
    message.attach(MIMEText(format_email_body(complaint_data, department, user_email, authority_advice), "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            recipients = [to_email] + ([user_email] if user_email else [])
            server.send_message(message, to_addrs=recipients)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
