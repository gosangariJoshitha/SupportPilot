from rag.llm_generator import generate_resolution

class ResolutionAgent:
    @staticmethod
    def resolve(diagnosis, retrieval):
        """
        Uses existing OpenRouter logic. Validates sources strictly.
        """
        if not retrieval["results"]:
            return {
                "status": "INSUFFICIENT_KNOWLEDGE",
                "likely_cause": "",
                "troubleshooting_steps": [],
                "recommended_resolution": "No sufficiently relevant knowledge-base articles were found. More investigation is required.",
                "source_ids": [],
                "error": None
            }
            
        analysis = {
            "ticket_id": diagnosis.get("ticket_id", "Unknown"),
            "query": diagnosis.get("query", ""),
            "category": diagnosis.get("category", "General"),
            "severity": diagnosis.get("severity", "Medium"),
            "priority": diagnosis.get("priority", "P3"),
            "keywords": []
        }
        
        result = generate_resolution(analysis, retrieval["results"], retrieval["context"])
        
        # Additional safety check on source IDs
        valid_ids = {doc["id"] for doc in retrieval["results"]}
        validated_sources = []
        for src in result.get("source_ids", []):
            if src in valid_ids:
                validated_sources.append(src)
                
        result["source_ids"] = validated_sources
        
        return result
