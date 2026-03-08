import traceback
from pathlib import Path

LOG_DIR = Path("logs")


def collect_recent_logs(lines=200):
    log_file = LOG_DIR / "logis.log"

    if not log_file.exists():
        return "No log file found."

    with open(log_file, "r", encoding="utf-8") as f:
        content = f.readlines()

    return "".join(content[-lines:])


def build_debug_prompt(error, context=""):
    logs = collect_recent_logs()

    prompt = f"""
You are Logis, an AI system debugging itself.

ERROR:
{error}

CONTEXT:
{context}

RECENT LOGS:
{logs}

TASK:
1. Explain the problem
2. Identify the likely cause
3. Suggest a fix
4. Suggest what file to check

Respond clearly.
"""

    return prompt


def debug_error(error, context=""):

    from core.ai_engine import ask_ai   # ← moved here

    prompt = build_debug_prompt(error, context)

    response = ask_ai(prompt)

    return response