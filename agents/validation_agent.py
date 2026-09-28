class ValidationAgent:
    @staticmethod
    def validate(ticket, diagnosis, retrieval, resolution):
        """
        Implements exactly the 40/40/20 formula and M4 Escalation Rules.
        """
        diag_conf = diagnosis.get("confidence", 0.0)
        ret_score = retrieval.get("top_score", 0.0)
        
        # Base confidence calculation
        steps = resolution.get("troubleshooting_steps", [])
        num_steps = len(steps)
        res_completeness = min(num_steps / 6.0, 1.0)
        
        # 40/40/20 formula
        score = (diag_conf * 0.40) + (ret_score * 0.40) + (res_completeness * 0.20)
        final_confidence = round(score * 100, 2)
        
        # Prepare standard validation info
        val_info = {
            "diagnosis_confidence": diag_conf,
            "retrieval_similarity": ret_score,
            "resolution_completeness": res_completeness,
            "threshold": 70.0,
            "final_confidence": final_confidence,
            "confidence": final_confidence
        }
        
        # M4 Escalation Rules Check
        priority = ticket.get("priority", "Low")
        repeated_attempts = ticket.get("repeated_attempts", 0)
        customer_requested_human = ticket.get("customer_requested_human", False)
        
        if priority == "Critical":
            val_info.update({"decision": "ESCALATE", "reason": "CRITICAL_PRIORITY"})
            return val_info
            
        if customer_requested_human:
            val_info.update({"decision": "ESCALATE", "reason": "CUSTOMER_REQUESTED_HUMAN"})
            return val_info
            
        if repeated_attempts >= 3:
            val_info.update({"decision": "ESCALATE", "reason": "REPEATED_ATTEMPTS"})
            return val_info
        
        # Resolution failure / insufficient knowledge
        if resolution.get("status") == "INSUFFICIENT_KNOWLEDGE":
            val_info.update({"decision": "ESCALATE", "reason": "INSUFFICIENT_KNOWLEDGE"})
            return val_info
            
        if resolution.get("status") == "ERROR" or resolution.get("error"):
            val_info.update({"decision": "ESCALATE", "reason": "LLM_FAILURE"})
            return val_info
            
        if not steps:
            val_info.update({"decision": "ESCALATE", "reason": "RESOLUTION_FAILED"})
            return val_info
            
        if retrieval["retrieved_count"] == 0 or retrieval["top_score"] < 0.02:
            val_info.update({"decision": "ESCALATE", "reason": "VALIDATION_FAILURE"})
            return val_info

        # Final AI confidence check
        if (final_confidence / 100.0) < 0.70:
            val_info.update({"decision": "ESCALATE", "reason": "LOW_AI_CONFIDENCE"})
        else:
            val_info.update({"decision": "AUTO_RESOLVE", "reason": "High confidence"})
            
        return val_info
