import os
import threading

from core.config import VECTORS_DIR, PROJECT_ROOT
from core.indexer import index_codebase
from tools.unity_watcher import unity_log_watcher
from tools.voice_system import vox_worker
from core.script_auto_indexer import auto_index_project_scripts


script_context_registry = {}


def start_indexer():
    """
    Ensures the codebase is indexed on startup.
    """
    try:
        if not os.listdir(VECTORS_DIR):
            print("[INDEXER] No vectors found. Indexing codebase...")
            index_codebase()
        else:
            print("[INDEXER] Existing vectors detected.")
    except Exception as e:
        print("[INDEXER] Failed:", e)


def start_script_indexer():
    """
    Initializes the script auto-indexer.
    """

    print("[SCRIPT INDEXER] Starting...")

    session_id = "system"

    auto_index_project_scripts(
        PROJECT_ROOT,
        script_context_registry,
        session_id
    )


def start_background_workers():

    print("[SYSTEM] Starting background workers...")

    threading.Thread(target=unity_log_watcher, daemon=True).start()
    threading.Thread(target=vox_worker, daemon=True).start()
    threading.Thread(target=start_indexer, daemon=True).start()
    threading.Thread(target=start_script_indexer, daemon=True).start()

    print("[SYSTEM] Background workers started.")