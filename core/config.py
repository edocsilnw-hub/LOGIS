import os

# Root of the Logis project
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Core directories
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
PROMPT_DEBUG_DIR = os.path.join(LOGS_DIR, "prompt_debug")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

# RAG system storage
VECTORS_DIR = os.path.join(DATA_DIR, "vectors")
SUMMARIES_DIR = os.path.join(DATA_DIR, "summaries")
CHUNKBLOCKS_DIR = os.path.join(DATA_DIR, "chunkblocks")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
CHUNKS_DIR = os.path.join(DATA_DIR, "chunks")

AI_CODE_PATH = PROJECT_ROOT

LLM_CONTEXT_SIZE = 8192

CONTEXT_BUDGET = {
    "system": 800,
    "memory": 1200,
    "rag": 3500,
    "history": 2000,
    "user": 500
}