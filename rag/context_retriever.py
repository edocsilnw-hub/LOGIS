import os
import json
import numpy as np

from core.config import PROJECT_ROOT, VECTORS_DIR
from core.ai_engine import get_embedding
from rag.chunk_processor import chunk_script


def retrieve_vector_context(query, top_k=5):

    import os
    import json
    import numpy as np

    from core.config import PROJECT_ROOT, VECTORS_DIR
    from core.ai_engine import get_embedding
    from rag.chunk_processor import chunk_script

    print(f"[RAG] Query received: {query}")

    registry_path = os.path.join(VECTORS_DIR, "vector_registry.json")

    if not os.path.exists(registry_path):
        print("[RAG ERROR] Vector registry missing.")
        return ""

    print("[RAG] Loading vector registry...")

    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    print(f"[RAG] Registry loaded. Scripts indexed: {len(registry)}")

    query_vec = np.array(get_embedding(query))

    print("[RAG] Query embedding generated.")

    scores = []

    for script, data in registry.items():

        if "chunks" not in data:
            continue

        print(f"[RAG] Scanning script: {script}")

        for chunk in data["chunks"]:

            vector_file = os.path.join(VECTORS_DIR, chunk["vector_file"])

            if not os.path.exists(vector_file):
                print(f"[RAG WARNING] Missing vector file: {vector_file}")
                continue

            vec = np.load(vector_file)

            similarity = np.dot(query_vec, vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(vec)
            )

            scores.append((similarity, script, chunk["chunk"]))

    print(f"[RAG] Total chunks scored: {len(scores)}")

    scores.sort(reverse=True)

    results = scores[:top_k]

    print(f"[RAG] Top {len(results)} results selected")

    context_blocks = []

    for score, script, chunk_id in results:

        print(f"[RAG] Loading chunk {chunk_id} from {script} | score={score:.4f}")

        script_path = os.path.join(PROJECT_ROOT, script)

        try:

            with open(script_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            chunks = chunk_script(content)

            if chunk_id < len(chunks):

                context_blocks.append(
                    f"\n--- SCRIPT: {script} | CHUNK {chunk_id} ---\n{chunks[chunk_id]}"
                )

        except Exception as e:
            print(f"[RAG ERROR] Failed loading script {script}: {e}")
            continue

    context = "\n".join(context_blocks)

    print(f"[RAG] Retrieved {len(context_blocks)} chunks for prompt")

    return context