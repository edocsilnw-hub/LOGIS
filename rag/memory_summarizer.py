import os

from core.ai_engine import call_ollama

def summarize_chunk_content(chunk_name, content):
    """Generates structured summary of a project chunk."""
    try:
        summary_prompt = (
            "You are summarizing a development log chunk.\n\n"
            "Summarize the following project log with:\n"
            "- Major goals worked on\n"
            "- Problems encountered\n"
            "- Solutions implemented\n"
            "- Architectural changes\n"
            "- Open issues remaining\n\n"
            "Keep under 5000 characters.\n\n"
            f"CHUNK NAME: {chunk_name}\n\n"
            f"{content}\n\n"
            "SUMMARY:"
        )

        summary, _ = call_ollama(summary_prompt)
        return summary

    except Exception as e:
        return f"[Chunk summary error: {e}]"
    
