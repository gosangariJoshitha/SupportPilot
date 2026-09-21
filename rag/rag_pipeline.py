import json
from rag.retriever import KnowledgeRetriever
from rag.ticket_analyzer import analyze_ticket
from rag.context_builder import build_context
from rag.llm_generator import generate_resolution

MIN_RELEVANCE = 0.30

_retriever = None

def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeRetriever()
    return _retriever

def retrieve_knowledge(query, top_k=3):
    retriever = get_retriever()
    results = retriever.search(query, top_k=top_k)
    return [r for r in results if r["score"] >= MIN_RELEVANCE]

def run_rag_pipeline(ticket_id, title, description, category=None, priority=None, chat_history=None):
    workflow_status = {
        "ticket_analysis": "pending",
        "knowledge_retrieval": "pending",
        "context_augmentation": "pending",
        "response_generation": "pending"
    }

    # Step 1: Ticket Analysis
    analysis = analyze_ticket(ticket_id, title, description, category, priority)
    workflow_status["ticket_analysis"] = "completed"

    # Step 2: Knowledge Base Retrieval
    retrieved_docs = retrieve_knowledge(analysis["query"], top_k=3)
    workflow_status["knowledge_retrieval"] = "completed"

    if not retrieved_docs:
        workflow_status["context_augmentation"] = "skipped"
        workflow_status["response_generation"] = "completed"
        resolution = {
            "status": "INSUFFICIENT_KNOWLEDGE",
            "likely_cause": "",
            "troubleshooting_steps": [],
            "recommended_resolution": "No sufficiently relevant knowledge-base articles were found. More investigation is required.",
            "source_ids": [],
            "error": None
        }
        return {
            "status": "INSUFFICIENT_KNOWLEDGE",
            "analysis": analysis,
            "retrieved_documents": [],
            "context": "",
            "resolution": json.dumps(resolution),
            "resolution_confidence": 0.0,
            "sources": [],
            "engine": "openrouter",
            "workflow_status": workflow_status
        }

    # Step 3: Context Augmentation
    context = build_context(retrieved_docs)
    workflow_status["context_augmentation"] = "completed"

    # Step 4: Resolution Generation via OpenRouter
    structured_result = generate_resolution(analysis, retrieved_docs, context, chat_history)
    workflow_status["response_generation"] = "completed"

    base_confidence = sum(doc["score"] for doc in retrieved_docs) / len(retrieved_docs)
    adjusted_confidence = min(max(base_confidence * 1.85, 0.75), 0.99)
    resolution_confidence = round(adjusted_confidence, 2)
    
    if structured_result.get("status") == "INSUFFICIENT_KNOWLEDGE" or structured_result.get("error"):
        resolution_confidence = 0.0

    return {
        "status": "OK" if not structured_result.get("error") else "ERROR",
        "analysis": analysis,
        "retrieved_documents": retrieved_docs,
        "context": context,
        "resolution": json.dumps(structured_result),
        "resolution_confidence": resolution_confidence,
        "sources": structured_result.get("source_ids", []),
        "engine": "openrouter",
        "workflow_status": workflow_status
    }
