def build_context(results):
    context = ""
    for result in results:
        content = result.get("content", "")
        context += f"""
Knowledge Base Article:
ID: {result['id']}
Title: {result['title']}
Relevance: {result['score']:.2f}

{content}

------------------------------
"""
    return context
