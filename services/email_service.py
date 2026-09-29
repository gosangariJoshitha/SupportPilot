import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests

def is_configured():
    has_resend = bool(os.environ.get("RESEND_API_KEY"))
    has_sendgrid = bool(os.environ.get("SENDGRID_API_KEY")) and bool(os.environ.get("SENDGRID_SENDER_EMAIL"))
    has_smtp = bool(os.environ.get("SMTP_EMAIL")) and bool(os.environ.get("SMTP_PASSWORD"))
    return has_resend or has_sendgrid or has_smtp

def send_resolution_email(ticket_data):
    """
    Sends a resolution email for AUTO_RESOLVED tickets.
    Returns:
        (status_string, error_message, sent_timestamp)
        status_string is one of: "SENT", "FAILED", "NOT_CONFIGURED"
    """
    if not is_configured():
        return "NOT_CONFIGURED", "Email integration is not configured.", None
        
    to_email = ticket_data.get("email")
    if not to_email:
        return "FAILED", "No recipient email provided.", None
        
    ticket_id = ticket_data.get("ticket_id")
    title = ticket_data.get("title")
    diagnosis = ticket_data.get("category", "General")
    
    resolution = ticket_data.get("structured_resolution", {})
    if not isinstance(resolution, dict):
        resolution = {}
        
    likely_cause = resolution.get("likely_cause", "Unknown cause")
    recommended_res = resolution.get("recommended_resolution", "")
    steps = resolution.get("troubleshooting_steps", [])
    
    # Format steps
    formatted_steps = ""
    for idx, step in enumerate(steps, 1):
        if isinstance(step, dict):
            formatted_steps += f"{idx}. {step.get('heading', '')}\n   {step.get('description', '')}\n"
        else:
            formatted_steps += f"{idx}. {step}\n"
            
    confidence = ticket_data.get("validation_confidence", 0.0)
    sources = ticket_data.get("structured_sources", [])
    sources_str = ", ".join(sources) if sources else "None"
    
    subject = f"Support Ticket Resolved — #{ticket_id}"
    body = f"""Hello,

Your support ticket has been analyzed by SupportPilot.

Issue:
{title}

Diagnosis:
{diagnosis}

Likely Cause:
{likely_cause}

Troubleshooting Steps:

{formatted_steps}

Recommended Resolution:
{recommended_res}

Resolution Confidence:
{confidence:.1f}%

Knowledge Sources:
{sources_str}

Regards,
SupportPilot AI Support
"""

    # OPTION 1: Resend HTTP API (Works on Render Free Tier)
    resend_api_key = os.environ.get("RESEND_API_KEY")
    if resend_api_key:
        try:
            headers = {
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "from": "SupportPilot <onboarding@resend.dev>",
                "to": [to_email],
                "subject": subject,
                "text": body
            }
            resp = requests.post("https://api.resend.com/emails", json=payload, headers=headers, timeout=10)
            if resp.status_code in [200, 201]:
                return "SENT", None, datetime.utcnow().isoformat()
            else:
                return "FAILED", f"Resend API Error: {resp.text}", None
        except Exception as e:
            return "FAILED", f"Resend Request Error: {str(e)}", None

    # OPTION 2: SendGrid HTTP API (Allows sending to ANY email if you verify a Single Sender)
    sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")
    sendgrid_sender = os.environ.get("SENDGRID_SENDER_EMAIL") # The email you verified on SendGrid
    if sendgrid_api_key and sendgrid_sender:
        try:
            headers = {
                "Authorization": f"Bearer {sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": sendgrid_sender, "name": "SupportPilot AI"},
                "subject": subject,
                "content": [{"type": "text/plain", "value": body}]
            }
            resp = requests.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers, timeout=10)
            if resp.status_code in [200, 201, 202]:
                return "SENT", None, datetime.utcnow().isoformat()
            else:
                return "FAILED", f"SendGrid API Error: {resp.text}", None
        except Exception as e:
            return "FAILED", f"SendGrid Request Error: {str(e)}", None

    # OPTION 3: Fallback to SMTP (Works locally, blocked on Render)
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_email = os.environ.get("SMTP_EMAIL")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    
    msg = MIMEMultipart()
    msg['From'] = smtp_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=5) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
            
        return "SENT", None, datetime.utcnow().isoformat()
    except Exception as e:
        return "FAILED", str(e), None
