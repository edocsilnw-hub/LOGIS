import os
import json
import numpy as np

from core.ai_engine import call_ollama
from core.config import VECTORS_DIR, SUMMARIES_DIR, CHUNKBLOCKS_DIR, PROJECT_ROOT
from core.ai_engine import get_embedding
from core.context_allocator import allocate_context
from rag.query_expansion import generate_search_queries
from rag.keyword_search import keyword_search
from rag.chunk_processor import split_into_chunks
from rag.memory_summarizer import summarize_chunk_content
from rag.graph_retriever import retrieve_graph_context
from rag.vector_index import vector_index

def load_importance_map():
    """
    Loads learned importance scores for project files. test test test test
    """
    path = os.path.join(VECTORS_DIR, "importance_map.json")

    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def find_best_context(user_query, top_n=2):
    if not os.path.exists(VECTORS_DIR):
        return ""
    queries = generate_search_queries(user_query)
    query_vectors = []

    for q in queries:
        vec = get_embedding(q)

        if vec is not None:
            query_vectors.append(np.array(vec))

    if not query_vectors:
        return ""

    rankings = []

    if not os.path.exists(VECTORS_DIR):
        return ""

    vector_files = [
        f for f in os.listdir(VECTORS_DIR)
        if f.endswith(".npy")
    ]
    print("VECTOR FILES FOUND:", len(vector_files))

    vector_files = vector_files[:300]  # safety cap

    dependency_map = load_dependency_map()
    importance_map = load_importance_map()
    code_graph = load_code_graph()  

    for f in vector_files:

        script_file = None

        path = os.path.join(VECTORS_DIR, f)
        chunk_vec = None
        content = ""

        f_lower = f.lower()

        # CODE VECTORS
        if f_lower.endswith("_code_vector.npy"):

            try:
                chunk_vec = np.load(path)
            except:
                continue

            meta_path = path.replace("_code_vector.npy", "_META.json")

            try:
                with open(meta_path, "r", encoding="utf-8") as mf:
                    meta = json.load(mf)

                script_path = meta.get("original_path")
                if not script_path:
                    continue
                script_file = meta.get("file_name")
                script_rel_path = os.path.relpath(script_path, PROJECT_ROOT)

            except:
                continue

            if os.path.exists(script_path):
                try:
                    with open(script_path, "r", encoding="utf-8", errors="ignore") as sf:
                        script_content = sf.read()

                    script_preview = script_content[:4000]

                    content = f"[SCRIPT]\n{script_rel_path}\n\n{script_preview}"

                    graph_context = retrieve_graph_context(script_rel_path, code_graph)

                    for g in graph_context:
                        content += "\n\n" + g

                except:
                    continue

            # RELATED SCRIPTS
            related = dependency_map.get(script_file, [])

            for rel in related:

                rel_script = rel + ".cs"
                rel_path = os.path.join(PROJECT_ROOT, "Assets", rel_script)

                if os.path.exists(rel_path):

                    try:
                        with open(rel_path, "r", encoding="utf-8", errors="ignore") as rf:
                            rel_content = rf.read()

                        rel_preview = rel_content[:2000]

                        content += (
                            f"\n\n[RELATED SCRIPT]\n{rel_script}\n\n{rel_preview}"
                        )

                    except:
                        pass

        # LOG SUMMARY VECTORS
        elif f_lower.endswith("_vector.npy"):

            try:
                chunk_vec = np.load(path)
            except:
                continue

            summary_name = f.replace("_vector.npy", "_summary.txt")
            summary_path = os.path.join(SUMMARIES_DIR, summary_name)

            if os.path.exists(summary_path):

                with open(summary_path, "r", encoding="utf-8") as file:
                    content = file.read()

        # SIMILARITY
        if chunk_vec is not None and content:

            best_similarity = 0

            for qv in query_vectors:

                denom = np.linalg.norm(qv) * np.linalg.norm(chunk_vec)
                if denom == 0:
                    continue

                similarity = np.dot(qv, chunk_vec) / denom

                if similarity > best_similarity:
                    best_similarity = similarity

        boost = 0

        # Boost if query mentions the script name
        if script_file and script_file.lower() in user_query.lower():
            boost += 0.15

        # Boost important project files
        importance_score = importance_map.get(script_file, 0)

        boost += importance_score * 0.2

        rankings.append((best_similarity + boost, script_file, content))

    if not rankings:
        return ""
    
    rankings.sort(key=lambda x: x[0], reverse=True)

    vector_results = [r[2] for r in rankings[:top_n]]

    keyword_results = [
        result[:2000]
        for result in keyword_search(user_query)[:top_n]
    ]

    combined = []

    seen = set()

    for item in vector_results + keyword_results:

        if item in seen:
            continue

        combined.append(item)
        seen.add(item)

    context_block = "\n\n[RELEVANT PROJECT MEMORY]\n"
    context_block += "\n---\n".join(combined)

    MAX_CONTEXT = 8000

    if len(context_block) > MAX_CONTEXT:
        context_block = context_block[:MAX_CONTEXT]

    distilled = distill_context(user_query, context_block)

    return distilled




def load_dependency_map():

    path = os.path.join(VECTORS_DIR, "dependency_map.json")

    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def load_code_graph():

    path = os.path.join(VECTORS_DIR, "code_graph.json")

    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def distill_context(user_query, rag_context):

    if not rag_context:
        return ""

    prompt = f"""
You are filtering project context for an AI coding assistant.

User Question:
{user_query}

Context:
{rag_context}

Extract ONLY the information needed to answer the question.
Remove unrelated details.

Return a concise technical context summary.
"""

    try:
        distilled, _ = call_ollama(prompt)
        return distilled
    except:
        return rag_context[:4000]
    
def retrieve_ranked_context(queries, max_chunks=3):

    candidates = []

    for q in queries[:3]:

        # VECTOR SEARCH
        try:
            query_vec = np.array(get_embedding(q))
            vector_hits = vector_index.search(query_vec, top_k=3)

            for hit in vector_hits:
                candidates.append((1.0, hit[1]["vector_file"]))

        except:
            pass

        # FALLBACK
        result = find_best_context(q)

        if result:
            score = len(result)
            candidates.append((score, result))

    candidates.sort(reverse=True)

    return [c[1] for c in candidates[:max_chunks]]
