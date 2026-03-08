import os
from core.ai_engine import call_ollama


MAX_FILE_SIZE = 200000  # 200 KB safety limit


def summarize_script(script_name, content):
    """
    Uses the AI engine to summarize a script for quick context retrieval.
    """

    # prevent token overflow
    content = content[:8000]

    prompt = (
        "Summarize this Python file for an AI coding assistant.\n\n"
        "Include:\n"
        "- Purpose\n"
        "- Key classes\n"
        "- Key functions\n"
        "- Important behaviors\n\n"
        f"FILE: {script_name}\n\n"
        f"{content}\n\n"
        "SUMMARY:"
    )

    summary, _ = call_ollama(prompt)

    return summary


def auto_index_project_scripts(project_root, script_context_registry, session_id):
    """
    Scans a project directory, summarizes Python scripts,
    and registers them for AI context retrieval.
    """

    print(f"[SCRIPT INDEXER] Scanning project: {project_root}")

    ignore_dirs = {
        "venv",
        "__pycache__",
        ".git",
        "node_modules",
        "Library",
        "Temp",
        "Build"
    }

    if session_id not in script_context_registry:
        script_context_registry[session_id] = {
            "_active_list": [],
            "_mode": "summary"
        }

    registry = script_context_registry[session_id]

    indexed_count = 0

    for root, dirs, files in os.walk(project_root):

        # skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:

            if not file.endswith(".py"):
                continue

            path = os.path.join(root, file)

            try:

                # skip extremely large files
                if os.path.getsize(path) > MAX_FILE_SIZE:
                    print(f"[SKIP LARGE FILE] {file}")
                    continue

                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                summary = summarize_script(file, content)

                rel_path = os.path.relpath(path, project_root)

                registry[rel_path] = {
                    "summary": summary,
                    "full": content,
                    "path": path
                }

                if rel_path not in registry["_active_list"]:
                    registry["_active_list"].append(rel_path)

                indexed_count += 1

                print(f"[SCRIPT INDEXED] {rel_path}")

            except Exception as e:
                print(f"[INDEX ERROR] {file}: {e}")

    print(f"[SCRIPT INDEX COMPLETE] {indexed_count} files indexed.")