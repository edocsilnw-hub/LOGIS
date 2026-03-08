import os
from core.config import SUMMARIES_DIR

def keyword_search(query, top_n=2):
    """
    Simple keyword search across summaries.
    """
    results = []

    query_words = query.lower().split()

    if not os.path.exists(SUMMARIES_DIR):
        return []

    for file in os.listdir(SUMMARIES_DIR):

        if not file.endswith(".txt"):
            continue

        path = os.path.join(SUMMARIES_DIR, file)

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(4000).lower()

            score = sum(word in content for word in query_words)

            if score > 0:
                results.append((score, content))

        except:
            continue

    results.sort(key=lambda x: x[0], reverse=True)

    return [r[1] for r in results[:top_n]]