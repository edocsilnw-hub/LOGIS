import json
from core.ai_engine import call_ollama
from core.memory_manager import store_memory_vector


def extract_reasoning_memories(user_input, ai_output):

    prompt = f"""
You are a cognitive extraction system.

Analyze the conversation and extract structured reasoning memories.

Return JSON with:

patterns:
repeated ideas or behaviors

relationships:
connections between concepts

concepts:
important topics introduced

anomalies:
unexpected or contradictory ideas

Conversation:

USER:
{user_input}

AI:
{ai_output}

Return ONLY valid JSON.
"""

    try:

        response, _ = call_ollama(prompt)

        text = response

        start = text.find("{")
        end = text.rfind("}") + 1

        if start != -1:
            text = text[start:end]

        return json.loads(text)

    except Exception as e:

        print("[COGNITION ERROR]", e)

        return None


def store_reasoning_memories(memories):

    if not memories:
        return

    for category, items in memories.items():

        if not isinstance(items, list):
            continue

        for item in items:

            store_memory_vector(
                text=item,
                category=f"reasoning_{category}"
            )