from rag.retriever import KnowledgeRetriever
from rag.context_builder import build_context

# Reuse existing retriever
_retriever = None

def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeRetriever()
    return _retriever

class RetrievalAgent:
    MIN_RELEVANCE = 0.30

    @staticmethod
    def retrieve(query, top_k=3):
        """
        Retrieves knowledge using existing M2 retriever.
        """
        retriever = get_retriever()
        results = retriever.search(query, top_k=top_k)
        
        valid_results = [r for r in results if r["score"] >= RetrievalAgent.MIN_RELEVANCE]
        
        return {
            "results": valid_results,
            "top_score": valid_results[0]["score"] if valid_results else 0.0,
            "retrieved_count": len(valid_results),
            "context": build_context(valid_results) if valid_results else ""
        }
