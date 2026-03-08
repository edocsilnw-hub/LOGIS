from core.ai_engine import call_ollama


def plan_retrieval(user_query):

    planning_prompt = f"""
You are a system planner.

Decide which memory sources should be searched.

Available sources:
- project_logs
- codebase_scripts
- session_history
- unity_errors

User query:
{user_query}

Return a comma separated list.
"""

    try:
        response, _ = call_ollama(planning_prompt)

        sources = [s.strip().replace(".", "") for s in response.split(",")]

        return sources

    except Exception as e:
        print("[REASONING] Retrieval planner failed:", e)
        return ["codebase_scripts"]
    
def reflection_fix(response_text, *args, **kwargs):
    """
    Basic self-reflection cleanup step.
    Can later be expanded into a reasoning repair stage.
    """
    if not response_text:
        return response_text

    cleaned = response_text.strip()

    # remove duplicated sentences
    lines = cleaned.split("\n")
    seen = set()
    unique_lines = []

    for line in lines:
        if line not in seen:
            unique_lines.append(line)
            seen.add(line)

    return "\n".join(unique_lines)