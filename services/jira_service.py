import os
import requests
import json
from requests.auth import HTTPBasicAuth
from datetime import datetime

def is_configured():
    return bool(os.environ.get("JIRA_URL")) and \
           bool(os.environ.get("JIRA_EMAIL")) and \
           bool(os.environ.get("JIRA_API_TOKEN")) and \
           bool(os.environ.get("JIRA_PROJECT_KEY"))

def map_priority(priority_str):
    # SupportPilot uses Critical, High, Medium, Low for Severity and P1-P4 for Priority
    # Jira typically uses Highest, High, Medium, Low, Lowest. 
    # We will map our P1-P4 to generic Jira Priority names for a default schema.
    mapping = {
        "P1": "Highest",
        "P2": "High",
        "P3": "Medium",
        "P4": "Low"
    }
    return mapping.get(priority_str, "Medium")

def create_issue(ticket_data, include_priority=True):
    """
    Creates a Jira issue for ESCALATED tickets.
    Returns:
        (status_string, error_message, issue_key, issue_url)
        status_string is one of: "CREATED", "FAILED", "NOT_CONFIGURED"
    """
    if not is_configured():
        return "NOT_CONFIGURED", "Jira integration is not configured.", None, None
        
    jira_url = os.environ.get("JIRA_URL").rstrip('/')
    jira_email = os.environ.get("JIRA_EMAIL")
    jira_token = os.environ.get("JIRA_API_TOKEN")
    project_key = os.environ.get("JIRA_PROJECT_KEY")
    
    ticket_id = ticket_data.get("ticket_id", "Unknown")
    title = ticket_data.get("title", "No Title")
    description = ticket_data.get("description", "No Description")
    category = ticket_data.get("category", "General")
    severity = ticket_data.get("severity", "Medium")
    priority = ticket_data.get("priority", "P3")
    
    m1_diagnosis = category
    m1_confidence = ticket_data.get("confidence", 0.0) * 100
    
    validation_confidence = ticket_data.get("validation_confidence", 0.0)
    escalation_reason = ticket_data.get("escalation_reason", "Low confidence")
    
    sources = ticket_data.get("structured_sources", [])
    sources_str = ", ".join(sources) if sources else "None"
    
    ai_resolution_raw = ticket_data.get("ai_resolution", "No AI resolution generated.")
    
    jira_description = f"""
*SupportPilot Ticket ID*: #{ticket_id}
*Title*: {title}
*Category*: {category}
*Severity*: {severity}
*Priority*: {priority}
*M1 Confidence*: {m1_confidence:.1f}%

*Ticket Description*:
{description}

*Retrieved KB Articles*: {sources_str}
*Validation Confidence*: {validation_confidence:.1f}%
*Escalation Reason*: {escalation_reason}

*AI-Generated Information*:
{ai_resolution_raw}
"""
    
    payload = {
        "fields": {
            "project": {
                "key": project_key
            },
            "summary": f"[SupportPilot] {title}",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": jira_description
                            }
                        ]
                    }
                ]
            },
            "issuetype": {
                "name": "Task" # Use a standard issue type that usually exists
            }
        }
    }
    
    if include_priority:
        payload["fields"]["priority"] = {
            "name": map_priority(priority)
        }
        
    url = f"{jira_url}/rest/api/3/issue"
    auth = HTTPBasicAuth(jira_email, jira_token)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, auth=auth, headers=headers, timeout=10)
        
        if response.status_code == 201:
            data = response.json()
            issue_key = data.get("key")
            issue_url = f"{jira_url}/browse/{issue_key}"
            return "CREATED", None, issue_key, issue_url
            
        elif response.status_code == 400 and include_priority:
            # Check if it failed because of priority field rejection
            error_data = response.json()
            error_messages = str(error_data.get("errors", {}))
            if "priority" in error_messages.lower():
                # Retry without priority
                return create_issue(ticket_data, include_priority=False)
                
        return "FAILED", f"Jira API Error ({response.status_code}): {response.text}", None, None
        
    except Exception as e:
        return "FAILED", f"Network or processing error: {str(e)}", None, None
