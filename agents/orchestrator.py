import json
import time
from datetime import datetime
from database import update_m3_workflow_state, get_ticket
from agents.diagnosis_agent import DiagnosisAgent
from agents.retrieval_agent import RetrievalAgent
from agents.resolution_agent import ResolutionAgent
from agents.validation_agent import ValidationAgent
from agents.escalation_agent import EscalationAgent
from services.email_service import send_resolution_email

class SupportPilotOrchestrator:
    @staticmethod
    def process_ticket(ticket_id, user_id):
        start_time = time.time()
        
        # 1. Fetch Ticket
        ticket = get_ticket(ticket_id, user_id)
        if not ticket:
            return {"error": "Ticket not found"}
            
        # Strict Idempotency Check
        if ticket.get("resolution_decision") in ["AUTO_RESOLVE", "ESCALATE"]:
            return ticket
            
        # Increment repeated_attempts if we are re-processing
        # This gets updated before diagnosis.
        from database import get_connection, execute_query
        conn = get_connection()
        cursor = conn.cursor()
        execute_query(cursor, "UPDATE tickets SET repeated_attempts = COALESCE(repeated_attempts, 0) + 1 WHERE ticket_id = ?", (ticket_id,))
        conn.commit()
        conn.close()
        
        # Reload ticket to get updated attempt count
        ticket = get_ticket(ticket_id, user_id)
            
        # Initialize Trace
        workflow_trace = []
        
        def log_trace(agent, status, extra=None):
            entry = {
                "agent": agent,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            if extra:
                entry.update(extra)
            workflow_trace.append(entry)
            
            # Persist intermediate state
            update_m3_workflow_state(ticket_id, user_id, {
                "workflow_trace": json.dumps(workflow_trace)
            })

        update_m3_workflow_state(ticket_id, user_id, {"workflow_status": "ANALYZING"})
        
        # 2. Diagnosis
        diagnosis = DiagnosisAgent.diagnose(
            ticket_id, 
            ticket["title"], 
            ticket["description"], 
            ticket.get("business_impact", "Low")
        )
        diagnosis["ticket_id"] = ticket_id
        
        log_trace("DiagnosisAgent", "completed", {
            "category": diagnosis["category"],
            "severity": diagnosis["severity"],
            "priority": diagnosis["priority"],
            "confidence": diagnosis["confidence"]
        })
        
        update_m3_workflow_state(ticket_id, user_id, {"workflow_status": "RETRIEVING"})
        
        # 3. Retrieval
        retrieval = RetrievalAgent.retrieve(diagnosis["query"])
        
        log_trace("RetrievalAgent", "completed", {
            "result_count": retrieval["retrieved_count"],
            "top_score": retrieval["top_score"],
            "retrieved_ids": [r["id"] for r in retrieval["results"]]
        })
        
        update_m3_workflow_state(ticket_id, user_id, {"workflow_status": "GENERATING"})
        
        # 4. Resolution
        resolution = ResolutionAgent.resolve(diagnosis, retrieval)
        
        log_trace("ResolutionAgent", "completed", {
            "status": resolution.get("status", "UNKNOWN"),
            "source_ids": resolution.get("source_ids", [])
        })
        
        update_m3_workflow_state(ticket_id, user_id, {"workflow_status": "VALIDATING"})
        
        # 5. Validation
        validation = ValidationAgent.validate(ticket, diagnosis, retrieval, resolution)
        
        log_trace("ValidationAgent", "completed", {
            "confidence": validation["confidence"],
            "decision": validation["decision"],
            "reason": validation["reason"],
            "diagnosis_confidence": validation.get("diagnosis_confidence"),
            "retrieval_similarity": validation.get("retrieval_similarity"),
            "resolution_completeness": validation.get("resolution_completeness")
        })
        
        process_time = time.time() - start_time
        
        # Prepare updates
        updates = {
            "ai_resolution": json.dumps(resolution),
            "resolution_confidence": validation["confidence"] / 100.0, # Store as 0-1 for backwards compat
            "resolution_sources": json.dumps(resolution.get("source_ids", [])),
            "resolution_engine": "openrouter",
            "validation_confidence": validation["confidence"],
            "validation_details": json.dumps(validation),
            "resolution_decision": validation["decision"],
            "escalation_reason": validation["reason"],
            "status": "Resolved" if validation["decision"] == "AUTO_RESOLVE" else "Escalated",
            "ai_response_time": process_time
        }
        
        if validation["decision"] == "AUTO_RESOLVE":
            updates["resolved_at"] = datetime.utcnow().isoformat()
        
        # Update local ticket object so integration agents have fresh data
        ticket.update(updates)
        ticket["structured_resolution"] = resolution
        ticket["structured_sources"] = resolution.get("source_ids", [])
        
        update_m3_workflow_state(ticket_id, user_id, updates)
        
        # 6. Integrations (Decision)
        if validation["decision"] == "AUTO_RESOLVE":
            update_m3_workflow_state(ticket_id, user_id, {"workflow_status": "AUTO_RESOLVED"})
            email_status, email_error, sent_at = send_resolution_email(ticket)
            
            updates["email_status"] = email_status
            updates["email_sent_at"] = sent_at
            updates["email_error"] = email_error
            
            log_trace("EmailService", "completed" if email_status == "SENT" else "failed", {
                "email_status": email_status,
                "error": email_error
            })
            
            log_trace("EscalationAgent", "not_required")
            
        else: # ESCALATE
            update_m3_workflow_state(ticket_id, user_id, {"workflow_status": "ESCALATED"})
            esc_result = EscalationAgent.escalate(ticket)
            
            updates["jira_issue_key"] = esc_result.get("issue_key")
            updates["jira_issue_url"] = esc_result.get("issue_url")
            
            log_trace("EscalationAgent", "completed" if esc_result["status"] == "CREATED" else "failed", {
                "jira_status": esc_result["status"],
                "error": esc_result.get("error")
            })
            log_trace("EmailService", "not_required")
            
        updates["workflow_trace"] = json.dumps(workflow_trace)
        update_m3_workflow_state(ticket_id, user_id, updates)
        
        final_ticket = get_ticket(ticket_id, user_id)
        if final_ticket:
            final_ticket["email_error"] = updates.get("email_error")
        return final_ticket
