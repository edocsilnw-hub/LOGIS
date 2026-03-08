import os
from datetime import datetime

from sympy import content

from core.config import (
    DATA_DIR,
    LOGS_DIR,
    VECTORS_DIR,
    CHUNKS_DIR,
    CHUNKBLOCKS_DIR,
    SUMMARIES_DIR
)

from rag.chunk_processor import split_into_chunks
from rag.memory_summarizer import summarize_chunk_content


SESSIONS_DIR = os.path.join(LOGS_DIR, "Sessions")
ACTIVE_DIR = os.path.join(LOGS_DIR, "Active")

UNITY_ERRORS_DIR = os.path.join(LOGS_DIR, "UnityErrors")
FULLCHUNKS_DIR = os.path.join(DATA_DIR, "FullChunks")

PROJECTS_DIR = os.path.join(DATA_DIR, "Projects")

def initialize_memory():

    ALL_MEMORY_DIRS = [
        LOGS_DIR,
        SESSIONS_DIR,
        ACTIVE_DIR,
        CHUNKS_DIR,
        CHUNKBLOCKS_DIR,
        SUMMARIES_DIR,
        VECTORS_DIR,
        UNITY_ERRORS_DIR,
        FULLCHUNKS_DIR,
        PROJECTS_DIR
    ]

    for folder in ALL_MEMORY_DIRS:
        os.makedirs(folder, exist_ok=True)

    print("[SYSTEM] Memory directories initialized.")

def diagnostic_memory_check():

    print("\n[DIAGNOSTIC] Memory Structure Check\n")

    ALL_MEMORY_DIRS = [
        LOGS_DIR,
        SESSIONS_DIR,
        ACTIVE_DIR,
        CHUNKS_DIR,
        CHUNKBLOCKS_DIR,
        SUMMARIES_DIR,
        VECTORS_DIR,
        UNITY_ERRORS_DIR
    ]

    seen = set()

    for folder in ALL_MEMORY_DIRS:

        print(f"Checking: {folder}")

        if folder in seen:
            print("  ⚠ WARNING: Duplicate directory reference")
        else:
            seen.add(folder)

        if os.path.exists(folder):
            print("  ✔ Exists")
        else:
            print("  ✖ Missing")

        if os.path.isdir(folder):
            print("  ✔ Is directory")
        else:
            print("  ✖ Not a directory")

        print()

    print("[DIAGNOSTIC COMPLETE]\n")

def extract_chunk_number(filename):
    try:
        return int(filename.replace("CHUNK_", "").replace(".txt", ""))
    except:
        return 0

def get_latest_chunk_path():
    """Finds or creates the latest CHUNK_X.txt file."""
    chunks = []

    if not os.path.exists(CHUNKS_DIR):
        os.makedirs(CHUNKS_DIR, exist_ok=True)

    for f in os.listdir(CHUNKS_DIR):
        parts = f.replace(".txt", "").split("_")
        if len(parts) == 2 and parts[1].isdigit():
            chunks.append(f)

    if not chunks:
        path = os.path.join(CHUNKS_DIR, "CHUNK_1.txt")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write("--- LOGIS PROGRESS TRACKER | CHUNK 1 ---\n")
        return path

    chunks.sort(key=extract_chunk_number)
    return os.path.join(CHUNKS_DIR, chunks[-1])

def auto_logger(user_input, ai_output, session_file, source_script="LLM"):
    """Logs everything to specific session and global chunks."""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Determine entry type
    if "error" in user_input.lower():
        entry_type = "debugging"
    elif "script" in user_input.lower():
        entry_type = "code"
    else:
        entry_type = "development"

    user_entry = (
        f"\n[{timestamp}]\n"
        f"ROLE: USER\n"
        f"TYPE: {entry_type}\n"
        f"CONTENT:\n{user_input}\n"
    )

    ai_entry = (
        f"\n[{timestamp}]\n"
        f"ROLE: AI\n"
        f"TYPE: response\n"
        f"CONTENT:\n{ai_output}\n"
    )

    log_entry = user_entry + ai_entry + "\n==================================================\n"

    # Write to session log
    with open(session_file, "a+", encoding="utf-8") as f:
        f.write(log_entry)

    chunk_path = get_latest_chunk_path()
    CHUNK_LIMIT = 120000

    current_size = os.path.getsize(chunk_path) if os.path.isfile(chunk_path) else 0

    # FIX: Only split and summarize the chunk when it reaches the limit (Rollover)
    if current_size >= CHUNK_LIMIT or current_size + len(log_entry) > CHUNK_LIMIT:
        
        # 1. Process the OLD chunk before moving to a new one
        with open(chunk_path, "r", encoding="utf-8") as f:
            full_text_to_index = f.read()
        
        session_id = os.path.basename(session_file).replace(".txt","")
        # This splits the 120kb chunk into 5kb blocks and vectorizes them
        split_into_chunks(session_id, full_text_to_index, chunk_path)

        # 2. Create the new chunk file
        current_num = int(os.path.basename(chunk_path).split("_")[1].split(".")[0])
        new_chunk_path = os.path.join(CHUNKS_DIR, f"CHUNK_{current_num + 1}.txt")

        with open(new_chunk_path, "w", encoding="utf-8") as f:
            f.write(f"--- LOGIS PROGRESS TRACKER | CHUNK {current_num + 1} ---\n")
            f.write(log_entry)
    else:
        with open(chunk_path, "a+", encoding="utf-8") as f:
            f.write(log_entry)

        # Live summary update
        if os.path.getsize(chunk_path) > 20000:

            with open(chunk_path, "r", encoding="utf-8") as f:
                content = f.read()

            chunk_name = os.path.basename(chunk_path)
            summarize_chunk_content(chunk_name, content)

def log_unity_error(error_text):
    """Stores Unity errors separately for debugging memory."""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = (
        f"\n[{timestamp}]\n"
        f"TYPE: UNITY_ERROR\n"
        f"CONTENT:\n{error_text}\n"
        f"==================================================\n"
    )

    error_file = os.path.join(UNITY_ERRORS_DIR, "unity_errors.txt")

    with open(error_file, "a+", encoding="utf-8") as f:
        f.write(log_entry)

def create_new_project(project_name):

    project_name = project_name.strip().replace(" ", "_")

    project_path = os.path.join(PROJECTS_DIR, project_name)

    if os.path.exists(project_path):
        print(f"[SYSTEM] Project '{project_name}' already exists.")
        return False

    os.makedirs(project_path, exist_ok=True)

    memory_root = os.path.join(project_path, "Memory")
    logs_root = os.path.join(memory_root, "Logs")

    dirs = [
        logs_root,
        os.path.join(logs_root, "Chunks"),
        os.path.join(logs_root, "ChunkBlocks"),
        os.path.join(logs_root, "Summaries"),
        os.path.join(logs_root, "Sessions"),
        os.path.join(logs_root, "Active"),
        os.path.join(logs_root, "UnityErrors"),
        os.path.join(memory_root, "FullChunks")
    ]

    for d in dirs:
        os.makedirs(d, exist_ok=True)

    print(f"[SYSTEM] Project '{project_name}' created successfully.")

    return True

def store_memory_vector(text, vector=None, metadata=None, category=None):
    """
    Temporary vector storage stub used by cognition modules.
    Later this will connect to the real vector database.
    """

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = (
        f"\n[{timestamp}]\n"
        f"TYPE: VECTOR_MEMORY\n"
        f"TEXT:\n{text}\n"
        f"METADATA:\n{metadata}\n"
        f"==================================================\n"
    )

    vector_log = os.path.join(VECTORS_DIR, "vector_memory_log.txt")

    with open(vector_log, "a+", encoding="utf-8") as f:
        f.write(entry)

    return True