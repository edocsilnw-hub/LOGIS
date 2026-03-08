import os
from datetime import datetime
from core.config import LOGS_DIR

PROMPT_DEBUG_DIR = os.path.join(LOGS_DIR, "prompt_debug")


def save_prompt_snapshot(prompt, session_id="unknown"):
    """
    Save the full prompt sent to the LLM.
    Useful for debugging RAG, memory, and hallucination issues.
    """

    try:
        os.makedirs(PROMPT_DEBUG_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        filename = f"prompt_{timestamp}.txt"

        path = os.path.join(PROMPT_DEBUG_DIR, filename)

        entry = (
            "==== LOGIS PROMPT SNAPSHOT ====\n\n"
            f"TIME: {timestamp}\n"
            f"PROMPT LENGTH: {len(prompt)}\n\n"
            "--------------------------------\n"
            "FULL PROMPT SENT TO MODEL\n"
            "--------------------------------\n\n"
            f"{prompt}\n\n"
            "--------------------------------\n"
            "END PROMPT\n"
            "--------------------------------\n"
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write(entry)

        if len(prompt) > 6000:
            print("[LOGIS WARNING] Prompt approaching context limit")

        print(f"[PROMPT SNAPSHOT SAVED] {filename}")

    except Exception as e:
        print(f"[PROMPT DEBUGGER ERROR] {e}")

def debug_prompt_budget(sections):

    total = 0
    print("\n[PROMPT BUDGET]")

    for name, text in sections.items():

        if not text:
            continue

        size = len(text)
        total += size

        print(f"{name.upper():<10}: {size} chars")

    print(f"TOTAL      : {total} chars\n")