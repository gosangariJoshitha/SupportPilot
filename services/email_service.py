import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def is_configured():
    return bool(os.environ.get("SMTP_EMAIL")) and bool(os.environ.get("SMTP_PASSWORD"))

def send_resolution_email(ticket_data):
    """
    Sends a resolution email for AUTO_RESOLVED tickets.
    Returns:
        (status_string, error_message, sent_timestamp)
        status_string is one of: "SENT", "FAILED", "NOT_CONFIGURED"
    """
    if not is_configured():
        return "NOT_CONFIGURED", "Email integration is not configured.", None
        
    # Idempotency check should be done by the caller using db state
    
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_email = os.environ.get("SMTP_EMAIL")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    
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

    msg = MIMEMultipart()
    msg['From'] = smtp_email
    msg['To'] = to_email
    msg['Subject'] = f"Support Ticket Resolved — #{ticket_id}"
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
            
        return "SENT", None, datetime.utcnow().isoformat()
    except Exception as e:
        return "FAILED", str(e), None
