from flask import request, jsonify
import os
import traceback

from rag.context_retriever import retrieve_vector_context
from core.memory_manager import create_new_project
from core.prompt_guardrails import enforce_prompt_limit
from core.ai_engine import call_ollama
from core.memory_manager import auto_logger
from cognition.reasoning_memory import (
    extract_reasoning_memories,
    store_reasoning_memories
)
from core.script_auto_indexer import auto_index_project_scripts

pending_project_creation = None
last_rag_debug = {
    "queries": [],
    "context_size": 0
}
last_prompt_debug = ""
last_vector_context_size = 0

def register_ai_routes(app, config):

    SESSIONS_DIR = config["SESSIONS_DIR"]
    script_context_registry = config["script_context_registry"]
    current_session_info = config["current_session_info"]
    active_chunk_selection = config["active_chunk_selection"]

    generate_search_queries = config.get("generate_search_queries")
    retrieve_ranked_context = config.get("retrieve_ranked_context")
    compress_context = config.get("compress_context")
    find_best_context = config.get("find_best_context")
    get_last_entries = config["get_last_entries"]
    reflection_fix = config["reflection_fix"]
    logis_speak = config.get("logis_speak", lambda x: None)

    if not generate_search_queries or not retrieve_ranked_context or not compress_context:
        print("[WARNING] RAG functions not loaded")

    def should_use_rag(text):
        text = text.lower()

        keywords = [
            "script","file","code","class","function","method",
            "bug","error","fix","issue","trace","debug",
            "where","how","explain","why",
            "system","architecture","module","pipeline",
            "vector","embedding","retrieval","rag"
        ]

        return len(text.split()) >= 3
    
    @app.errorhandler(Exception)
    def handle_global_error(error):

        print("[GLOBAL ERROR]")
        traceback.print_exc()

        return jsonify({
            "response": "[SYSTEM ERROR] Logis encountered an internal error."
        }), 500

    @app.route("/debug/prompt", methods=["GET"])
    def debug_prompt():
        return jsonify({
            "prompt_length": len(last_prompt_debug),
            "prompt": last_prompt_debug or "[No prompt generated yet]"
        })


    @app.route("/debug/system", methods=["GET"])
    def debug_system():

        return jsonify({
            "llm_configured": bool(call_ollama),
            "rag_queries_loaded": bool(generate_search_queries),
            "rag_retriever_loaded": bool(retrieve_ranked_context),
            "context_compressor_loaded": bool(compress_context),
            "session_system": bool(SESSIONS_DIR),
            "script_registry_loaded": bool(script_context_registry),
            "active_chunks": len(active_chunk_selection),
            "prompt_debug_ready": bool(last_prompt_debug),
            "find_best_context_loaded": bool(find_best_context)
        })

    @app.route("/debug/rag", methods=["GET"])
    def debug_rag():
        return jsonify(last_rag_debug)
        
    @app.route("/debug/selftest", methods=["GET"])
    def debug_selftest():

        test_prompt = "Explain how the vector_index system works."

        try:
            response, _ = call_ollama(test_prompt)
            status = "ok"
        except Exception:
            status = "failed"

        return jsonify({
            "llm_status": status
        })

    @app.route("/debug/health", methods=["GET"])
    def debug_health():

        health = {
            "llm": "unknown",
            "rag_query_generator": bool(generate_search_queries),
            "rag_retriever": bool(retrieve_ranked_context),
            "context_compressor": bool(compress_context),
            "memory_system": False,
            "session_logging": False
        }

        # Test LLM
        try:
            response, _ = call_ollama("Reply with the word OK.")
            if response and "ok" in response.lower():
                health["llm"] = "ok"
            else:
                health["llm"] = "unexpected_response"
        except Exception:
            health["llm"] = "failed"

        # Test Session Logging
        try:
            test_file = os.path.join(SESSIONS_DIR, "health_test.txt")
            auto_logger("health test input", "health test output", test_file)

            if os.path.exists(test_file):
                health["session_logging"] = True
        except Exception:
            health["session_logging"] = False

        # Test Memory System
        try:
            test_memories = extract_reasoning_memories(
                "User is testing the memory system.",
                "The system successfully extracted reasoning memory."
            )

            store_reasoning_memories(test_memories)

            health["memory_system"] = True

        except Exception:
            health["memory_system"] = False

        return jsonify(health)

    @app.route("/debug/context", methods=["GET"])
    def debug_context():

        return jsonify({
            "vector_context_chars": last_vector_context_size,
            "active_scripts": len(script_context_registry),
            "active_chunks": len(active_chunk_selection),
            "sessions_dir": SESSIONS_DIR
        })

    import time

    @app.route("/debug/ping")
    def debug_ping():
        return jsonify({
            "status": "alive",
            "time": time.time()
        })

    @app.route("/predict", methods=["POST"])
    def predict():
        data = request.get_json() or {}
        if not isinstance(data, dict):
            return jsonify({"response": "Invalid request"})

        session_id = data.get("session_id", "default")

        if session_id not in script_context_registry:
            script_context_registry[session_id] = {"_active_list": [], "_mode": "summary"}

        user_input = str(data.get("prompt", ""))
        current_session_info["id"] = session_id

        session_file = os.path.join(SESSIONS_DIR, f"{session_id}.txt")

        vector_context = ""
        queries = []
        chunk_context = ""

        print("[RAG DEBUG] should_use_rag:", should_use_rag(user_input))
        print("[RAG DEBUG] prompt length:", len(user_input.strip()))
        print("[RAG DEBUG] functions:",
            bool(generate_search_queries),
            bool(retrieve_ranked_context),
            bool(compress_context))

        if should_use_rag(user_input) and len(user_input.strip()) > 12:

            if generate_search_queries and retrieve_ranked_context and compress_context:

                if len(user_input.split()) >= 3:
                    queries = generate_search_queries(user_input)
                    contexts = retrieve_ranked_context(queries)
                    vector_context = compress_context(contexts)

            if not vector_context and find_best_context:
                print("[RAG FALLBACK] Using semantic memory retrieval")
                vector_context = find_best_context(user_input)

            if not vector_context:
                print("[RAG FALLBACK] Using direct vector retrieval")
                vector_context = retrieve_vector_context(user_input)
            global last_rag_debug
            last_rag_debug = {"queries": queries, "context_size": len(vector_context)}

        global last_vector_context_size
        last_vector_context_size = len(vector_context)

        if session_id in active_chunk_selection:
            chunk_data = active_chunk_selection[session_id]
            if chunk_data.get("summary"):
                chunk_context = chunk_data["summary"]

        selected_script_content = ""
        session_scripts = script_context_registry.get(session_id, {})
        active_list = session_scripts.get("_active_list", [])
        mode = session_scripts.get("_mode", "summary")

        for script in active_list:
            script_data = session_scripts.get(script, {})
            header = f"\n\n[FILE {mode.upper()}: {script}]\n"

            if mode == "summary":
                content = script_data.get("summary", "")
            else:
                content = script_data.get("full", "")[:2000]

            selected_script_content += header + content

        if not selected_script_content.strip():
            selected_script_content = "[NO SCRIPT CONTEXT AVAILABLE]\nNo scripts are currently loaded."

        session_context = get_last_entries(session_file, max_entries=3)

        final_prompt = f"""SYSTEM: You are LOGIS (Logic-Oriented General Intelligence System), an advanced AI engineering assistant responsible for helping design, debug, and improve the LOGIS AI system.

        Your role is to collaborate with the user to build a robust, scalable, and intelligent AI architecture.

        ### CORE RESPONSIBILITIES

        SYSTEM ARCHITECTURE  
        Analyze and improve the structure of the LOGIS codebase. Suggest modular, scalable, and maintainable designs.

        DEBUGGING  
        Identify bugs, edge cases, and logic errors in scripts. Provide clear explanations and reliable fixes.

        CODE DEVELOPMENT  
        Write clean, production-quality Python code that integrates with the existing LOGIS architecture.

        SYSTEM INTELLIGENCE  
        Assist in improving memory systems, RAG pipelines, context management, reasoning layers, and internal tooling.

        ENGINEERING COLLABORATION  
        Work with the user as a senior AI engineer would: explain reasoning clearly and propose practical improvements.

        ### CONTEXT PRIORITY

        Use the following sources of information in this priority order:

        1. USER REQUEST
        2. ACTIVE SCRIPTS
        3. PROJECT MEMORY
        4. RECENT SESSION

        ACTIVE SCRIPTS contain currently loaded source code and represent the authoritative behavior of the system.

        PROJECT MEMORY contains retrieved summaries, notes, or previously extracted reasoning that may help answer the request.

        RECENT SESSION contains the most recent interaction history for conversational continuity.

        ### RESPONSE GUIDELINES

        • Be technically precise and concise  
        • Prefer concrete solutions over speculation  
        • When suggesting changes, explain why the change improves the system  
        • When writing code, ensure it integrates with the existing architecture  
        • Reference relevant scripts when possible

        Your objective is to help the user progressively improve the LOGIS system.

        ===== ACTIVE SCRIPTS =====
        {selected_script_content}

        ===== ACTIVE CHUNK =====
        {chunk_context}

        ===== PROJECT MEMORY =====
        {vector_context}

        ===== RECENT SESSION =====
        {session_context}

        ===== USER REQUEST =====
        {user_input}

        ===== LOGIS RESPONSE =====
        """

        final_prompt = enforce_prompt_limit(final_prompt)

        global pending_project_creation
        lower_prompt = user_input.lower()

        if "create project" in lower_prompt or "new project" in lower_prompt:
            project_name = user_input.lower()
            project_name = project_name.replace("create project", "")
            project_name = project_name.replace("new project", "")
            project_name = project_name.strip().replace(" ", "_").replace("-", "_")

            if not project_name:
                return jsonify({"response": "What would you like to name the project?"})

            pending_project_creation = project_name
            return jsonify({"response": f"Confirmed. Would you like me to create the project '{project_name}'? (yes/no)"})

        if pending_project_creation:
            if user_input.lower() in ["yes", "y", "confirm"]:
                success = create_new_project(pending_project_creation)
                if success:
                    auto_index_project_scripts(pending_project_creation)
                name = pending_project_creation
                pending_project_creation = None
                if success:
                    return jsonify({"response": f"Project '{name}' created successfully."})
                else:
                    return jsonify({"response": f"Project '{name}' already exists."})

            elif user_input.lower() in ["no", "cancel"]:
                name = pending_project_creation
                pending_project_creation = None
                return jsonify({"response": f"Project creation for '{name}' cancelled."})

        global last_prompt_debug
        last_prompt_debug = final_prompt

        print(f"[PROMPT SIZE] {len(final_prompt)} chars")
        if len(final_prompt) > 15000:
            print("[WARNING] Prompt nearing token limit")

        ollama_json = {}
        ai_output = ""

        try:
            ai_output, ollama_json = call_ollama(final_prompt)
            if ai_output and "```" in ai_output and len(ai_output) < 8000:
                ai_output = reflection_fix(user_input, ai_output)
        except Exception as e:
            ai_output = f"[MODEL ERROR] {e}"

        if isinstance(ollama_json, dict):
            print("OLLAMA RESPONSE:", {
                "model": ollama_json.get("model"),
                "eval_count": ollama_json.get("eval_count"),
                "done": ollama_json.get("done")
            })
        else:
            print("OLLAMA RESPONSE: invalid or empty")

        if not ai_output or not ai_output.strip():
            ai_output = "[Model returned empty response]"

        auto_logger(user_input, ai_output, session_file)

        if len(user_input) > 20:
            try:
                memories = extract_reasoning_memories(user_input, ai_output)
                store_reasoning_memories(memories)
            except Exception as e:
                print("[MEMORY ERROR]", e)

        try:
            logis_speak(ai_output)
        except Exception as e:
            print("[VOICE ERROR]", e)

        return jsonify({"response": ai_output})