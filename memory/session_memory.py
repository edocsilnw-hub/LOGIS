import os

ENTRY_SEPARATOR = "=================================================="


def get_last_entries(session_file, max_entries=5):
    """
    Retrieves the last X session entries for prompt context.
    """

    if not os.path.exists(session_file):
        return ""

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            content = f.read()

        entries = content.split(ENTRY_SEPARATOR)
        entries = [e.strip() for e in entries if e.strip()]

        last_entries = entries[-max_entries:]

        formatted_context = "\n\n[RECENT SESSION CONTEXT]\n"

        for entry in last_entries:
            formatted_context += entry + "\n\n---\n\n"

        return formatted_context

    except Exception as e:
        print("[SESSION MEMORY] Failed to read session:", e)
        return ""
