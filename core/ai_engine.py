import requests
import logging
import time
import uuid
import traceback

from tools.debug_tools import save_prompt_snapshot
from core.config import LLM_CONTEXT_SIZE

OLLAMA_HOST = "http://127.0.0.1:11434"

DEFAULT_MODEL = "llama3:8b"
EMBED_MODEL = "nomic-embed-text"

REQUEST_TIMEOUT = 120
MAX_RETRIES = 3


def call_ollama(prompt, model=DEFAULT_MODEL, temperature=0.2):
    if not prompt or not prompt.strip():
        return "[ERROR: Empty prompt]", {}

    prompt = prompt[:LLM_CONTEXT_SIZE * 3]

    url = f"{OLLAMA_HOST}/api/chat"
    request_id = str(uuid.uuid4())[:8]

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_ctx": LLM_CONTEXT_SIZE
        }
    }

    save_prompt_snapshot(prompt)

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()
            data = response.json()

            text = data.get("message", {}).get("content", "")
            return text, data

        except Exception as e:
            error_trace = traceback.format_exc()

            logging.warning(
                f"[AI_ENGINE][{request_id}] Ollama error attempt {attempt + 1}: {e}"
            )

            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
            else:
                return (
                    f"[LLM ERROR {request_id}]\n{str(e)}\n{error_trace}",
                    {}
                )


def check_ollama():
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def get_embedding(text, model=EMBED_MODEL):
    text = text[:4000]

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/embed",
            json={
                "model": model,
                "input": text
            },
            timeout=60
        )

        if response.status_code != 200:
            logging.error("[AI_ENGINE] Embedding request failed: %s", response.text)
            return None

        data = response.json()

        if "embeddings" in data and len(data["embeddings"]) > 0:
            return data["embeddings"][0]

        logging.error("[AI_ENGINE] Invalid embedding response: %s", data)
        return None

    except Exception as e:
        logging.error(f"[AI_ENGINE] Embedding error: {e}")
        return None


def compress_context(context_chunks, max_chars=12000):
    combined = ""

    for chunk in context_chunks:
        if not chunk:
            continue

        if len(combined) + len(chunk) > max_chars:
            break

        combined += chunk + "\n"

    return combined

def run_ai(prompt, context_chunks=None, temperature=0.2):
    """
    High-level AI call used by API routes.
    Handles context compression automatically.
    """

    context = ""

    if context_chunks:
        context = compress_context(context_chunks)

    final_prompt = f"""
Use the following context if relevant:

{context}

User:
{prompt}

Assistant:
"""

    response, meta = call_ollama(
        final_prompt,
        temperature=temperature
    )

    return response