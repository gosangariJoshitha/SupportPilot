"""
Milestone 2 - Knowledge Base Retrieval (the "R" in RAG).

TF-IDF + cosine similarity, exactly the approach from the PPT (slides 16-20).
This is intentionally simple and explainable rather than using embeddings -
the PPT explicitly recommends TF-IDF for this milestone (slide 43) and notes
embeddings as a future production upgrade.
"""

import json
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB_PATH = os.path.join("data", "knowledge_base.json")


class KnowledgeRetriever:
    def __init__(self, documents=None):
        if documents is None:
            documents = self._load_knowledge_base()

        self.documents = [self._normalize_document(doc) for doc in documents]

        self.texts = [
            doc["title"] + " " + doc["content"]
            for doc in self.documents
        ]

        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.document_vectors = self.vectorizer.fit_transform(self.texts)

    def _load_knowledge_base(self):
        with open(KB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _normalize_document(self, doc):
        normalized = dict(doc)

        parts = []
        if normalized.get("problem"):
            parts.append(normalized["problem"])
        if normalized.get("content"):
            parts.append(normalized["content"])
        if normalized.get("symptoms"):
            parts.extend(normalized["symptoms"])
        if normalized.get("solution"):
            for index, step in enumerate(normalized["solution"], start=1):
                parts.append(f"{index}. {step}")

        normalized["content"] = "\n".join(part.strip() for part in parts if str(part).strip())

        if not normalized["content"]:
            normalized["content"] = " ".join(
                str(value).strip()
                for value in [normalized.get("problem"), normalized.get("title")]
                if value
            )

        return normalized

    def search(self, query, top_k=3):
        query_vector = self.vectorizer.transform([query])

        scores = cosine_similarity(query_vector, self.document_vectors)[0]
        ranked_indices = scores.argsort()[::-1]

        results = []
        for index in ranked_indices[:top_k]:
            results.append({
                "id": self.documents[index]["id"],
                "title": self.documents[index]["title"],
                "category": self.documents[index]["category"],
                "content": self.documents[index]["content"],
                "score": float(scores[index])
            })

        return results
