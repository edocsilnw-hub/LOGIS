from core.config import CONTEXT_BUDGET


def trim_to_budget(text, max_chars):
    """Simple trim until tokenizer is added later."""
    if not text:
        return ""
    return text[:max_chars]


def allocate_context(system, memory, rag, history, user):

    system = trim_to_budget(system, CONTEXT_BUDGET["system"])
    memory = trim_to_budget(memory, CONTEXT_BUDGET["memory"])
    rag = trim_to_budget(rag, CONTEXT_BUDGET["rag"])
    history = trim_to_budget(history, CONTEXT_BUDGET["history"])
    user = trim_to_budget(user, CONTEXT_BUDGET["user"])

    prompt = f"""
[SYSTEM]
{system}

[MEMORY]
{memory}

[RAG CONTEXT]
{rag}

[CONVERSATION]
{history}

[USER]
{user}

[LOGIS]
"""

    return prompt