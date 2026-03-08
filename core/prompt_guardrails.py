MAX_PROMPT_CHARS = 20000

def enforce_prompt_limit(prompt, max_chars=MAX_PROMPT_CHARS):
    """
    Prevents prompt overflow while trying to preserve system instructions.
    """

    if len(prompt) <= max_chars:
        return prompt

    print("[GUARDRAIL] Prompt exceeded safe size. Trimming session context...")

    if "===== RECENT SESSION =====" in prompt:
        parts = prompt.split("===== RECENT SESSION =====")
        prompt = parts[0] + "\n===== RECENT SESSION =====\n[TRIMMED]\n"

    if len(prompt) > max_chars:
        prompt = prompt[-max_chars:]

    return prompt