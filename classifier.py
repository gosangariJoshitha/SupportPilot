import joblib
import json
import os
import re

class TicketClassifier:
    def __init__(self):
        self.model_path = os.path.join("models", "ticket_classifier.pkl")
        self.vectorizer_path = os.path.join("models", "vectorizer.pkl")
        self.metadata_path = os.path.join("models", "model_metadata.json")
        
        if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
            self.model = joblib.load(self.model_path)
            self.vectorizer = joblib.load(self.vectorizer_path)
        else:
            self.model = None
            self.vectorizer = None
            
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = None

    def preprocess(self, text):
        text = text.lower()
        # Remove unnecessary symbols but preserve IT terms
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def predict(self, text):
        if not self.model or not self.vectorizer:
            return "Unknown", 0.0
            
        clean_text = self.preprocess(text)
        vector = self.vectorizer.transform([clean_text])
        
        category = self.model.predict(vector)[0]
        
        # Calculate confidence
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(vector)[0]
            confidence = max(proba)
        else:
            # Fallback if probability is unavailable
            confidence = 0.85
            
        return category, float(confidence)

    def get_model_info(self):
        return self.metadata
