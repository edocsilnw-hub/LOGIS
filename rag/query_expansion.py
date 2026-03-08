from core.ai_engine import call_ollama

def generate_search_queries(user_query):
    """Generate multiple search queries for better RAG retrieval."""
    
    prompt = f"""
Generate 3 alternative search queries for retrieving technical information.

User Question:
{user_query}

Return each query on a new line.
"""

    try:
        result, _ = call_ollama(prompt)
        queries = [q.strip() for q in result.split("\n") if q.strip()]
        return [user_query] + queries[:3]

    except:
        return [user_query]