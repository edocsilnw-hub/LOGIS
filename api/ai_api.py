import os
import sys
import queue

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_cors import CORS

from core.ai_engine import run_ai
from core.config import (
    PROJECT_ROOT,
    DATA_DIR,
    SESSIONS_DIR,
    VECTORS_DIR,
    CHUNKBLOCKS_DIR,
    AI_CODE_PATH
)

from core.memory_manager import initialize_memory, auto_logger, log_unity_error
from core.script_auto_indexer import summarize_script, auto_index_project_scripts
from core.indexer import index_codebase

from memory.session_memory import get_last_entries

from cognition.reasoning_engine import plan_retrieval, reflection_fix

from rag.query_expansion import generate_search_queries
from rag.memory_summarizer import summarize_chunk_content
from rag.rag_engine import find_best_context
from rag.vector_index import vector_index

from routes.ai_routes import register_ai_routes

from tools.voice_system import logis_speak

app = Flask(__name__)
CORS(app)

initialize_memory()


# ============================================================
# RUNTIME STATE
# ============================================================

script_context_registry = {}
active_chunk_selection = {}
speech_queue = queue.Queue()

current_session_info = {"id": "default"}


# ============================================================
# BUILD CODE INTELLIGENCE INDEX
# ============================================================

print("[SYSTEM] Building code intelligence index...")
index_codebase()
print("[SYSTEM] Code index ready.")
vector_index()

# ============================================================
# BUILD SCRIPT SUMMARIES
# ============================================================

print("[SYSTEM] Building script summaries...")

auto_index_project_scripts(
    PROJECT_ROOT,
    script_context_registry,
    current_session_info["id"]
)

print("[SYSTEM] Script summaries ready.")


# ============================================================
# REGISTER API ROUTES
# ============================================================

register_ai_routes(app, {

    # ---------- PATHS ----------
    "SESSIONS_DIR": SESSIONS_DIR,
    "PROJECT_ROOT": PROJECT_ROOT,
    "CHUNKBLOCKS_DIR": CHUNKBLOCKS_DIR,
    "AI_CODE_PATH": AI_CODE_PATH,

    # ---------- STATE ----------
    "script_context_registry": script_context_registry,
    "active_chunk_selection": active_chunk_selection,
    "current_session_info": current_session_info,

    # ---------- RAG ----------
    "vector_index": vector_index,
    "generate_search_queries": generate_search_queries,
    "retrieve_ranked_context": find_best_context,

    # ---------- SUMMARIZERS ----------
    "summarize_script_content": summarize_script,
    "summarize_chunk_content": summarize_chunk_content,

    # ---------- MEMORY ----------
    "get_last_entries": get_last_entries,
    "auto_logger": auto_logger,

    # ---------- COGNITION ----------
    "plan_retrieval": plan_retrieval,
    "reflection_fix": reflection_fix,

    # ---------- AI ----------
    "run_ai": run_ai,

    # ---------- VOICE ----------
    "logis_speak": logis_speak
})


# ============================================================
# SERVER START
# ============================================================

if __name__ == "__main__":

    print("\n--- MASTER API ONLINE ---")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )