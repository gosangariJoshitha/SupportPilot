from classifier import TicketClassifier
from severity import predict_severity
from priority import calculate_priority

# Singleton or initialize on use
_classifier = None

def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = TicketClassifier()
    return _classifier

class DiagnosisAgent:
    @staticmethod
    def diagnose(ticket_id, title, description, business_impact="Low"):
        """
        Uses existing M1 classifier to diagnose the ticket.
        """
        classifier = get_classifier()
        combined_text = f"{title}. {description}"
        category, confidence = classifier.predict(combined_text)
        severity = predict_severity(combined_text)
        priority = calculate_priority(severity, business_impact)
        
        return {
            "category": category,
            "confidence": float(confidence),
            "severity": severity,
            "priority": priority,
            "query": combined_text
        }
