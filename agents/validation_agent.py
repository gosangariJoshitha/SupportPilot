class ValidationAgent:
    @staticmethod
    def validate(diagnosis, retrieval, resolution):
        """
        Implements exactly the 40/40/20 formula.
        """
        # Short-circuit if resolution failed or insufficient knowledge
        if resolution.get("status") == "INSUFFICIENT_KNOWLEDGE" or resolution.get("error"):
            return {
                "confidence": 0.0,
                "decision": "ESCALATE",
                "reason": "Insufficient Knowledge or Generation Error"
            }
            
        if not resolution.get("troubleshooting_steps"):
            return {
                "confidence": 0.0,
                "decision": "ESCALATE",
                "reason": "No troubleshooting steps generated"
            }
            
        if retrieval["retrieved_count"] == 0 or retrieval["top_score"] < 0.30:
            return {
                "confidence": 0.0,
                "decision": "ESCALATE",
                "reason": "Retrieval score below threshold"
            }

        diag_conf = diagnosis.get("confidence", 0.0)
        ret_score = retrieval.get("top_score", 0.0)
        
        steps = resolution.get("troubleshooting_steps", [])
        num_steps = len(steps)
        
        # 40/40/20 formula
        score = (diag_conf * 0.40) + (ret_score * 0.40) + (min(num_steps / 6.0, 1.0) * 0.20)
        final_confidence = round(score * 100, 2)
        
        if final_confidence >= 70.0:
            decision = "AUTO_RESOLVE"
            reason = "High confidence"
        else:
            decision = "ESCALATE"
            reason = "Confidence score below 70%"
            
        return {
            "confidence": final_confidence,
            "decision": decision,
            "reason": reason
        }
