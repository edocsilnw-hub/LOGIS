from flask import request, jsonify
import os


def register_script_routes(app, config):

    PROJECT_ROOT = config["PROJECT_ROOT"]
    script_context_registry = config["script_context_registry"]
    summarize_script_content = config["summarize_script_content"]

    @app.route("/list_scripts", methods=["GET"])
    def list_scripts():
        script_files = []
        for root, dirs, files in os.walk(PROJECT_ROOT):
            if any(x in root.split(os.sep) for x in ["venv", "Library", "obj", ".git", "__pycache__"]):
                continue
            for file in files:
                if file.endswith(".py") or file.endswith(".cs"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, PROJECT_ROOT).replace("\\", "/")
                    script_files.append(rel_path)

        return jsonify({"scripts": script_files})


    def filter_code_for_context(code_text, max_lines=150):
        """
        Trims boilerplate and keeps the 'Head' and 'Tail' of large files
        so the AI sees the Class definition and the most recent methods.
        """
        lines = code_text.split('\n')
        
        # Remove standard boilerplate
        filtered = [l for l in lines if not l.strip().startswith(("using System", "using UnityEngine.UI", "using TMPro"))]
        
        if len(filtered) > max_lines:
            head = filtered[:max_lines // 2]
            tail = filtered[-max_lines // 2:]
            return "\n".join(head) + "\n\n// ... [LOGIS: CONTENT TRIMMED TO SAVE TOKENS] ...\n\n" + "\n".join(tail)
        
        return "\n".join(filtered)

    @app.route("/load_scripts", methods=["POST"])
    def load_scripts():
        """Loads selected script contents into the registry."""
        try:
            data = request.get_json() or {}
            session_id = data.get("session_id")
            selected_scripts = data.get("selected_scripts", [])
            script_mode = data.get("script_mode", "summary") # Fixed key to match HTML

            if not session_id:
                return jsonify({"error": "No session_id provided"}), 400

            # Reset registry for clean load
            script_context_registry[session_id] = {
                "_active_list": [],
                "_mode": script_mode
            }

            normalized_root = os.path.abspath(PROJECT_ROOT)

            for script in selected_scripts:
                safe_path = os.path.abspath(os.path.join(PROJECT_ROOT, script))
                if (
                    os.path.isfile(safe_path)
                    and safe_path.lower().startswith(normalized_root.lower())
                    and (safe_path.endswith(".cs") or safe_path.endswith(".py"))
                ):
                    with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
                        full_content = f.read()

                    processed_content = full_content
                    
                    if len(full_content) > 8000:
                        processed_content = filter_code_for_context(full_content)

                    script_context_registry[session_id][script] = {
                        "full": processed_content,
                        "summary": None
                    }

                    # Generate summary only if in summary mode
                    if script_mode == "summary":
                        summary = summarize_script_content(script, full_content)
                        script_context_registry[session_id][script]["summary"] = summary

                    script_context_registry[session_id]["_active_list"].append(script)

            return jsonify({
                "status": "Success",
                "loaded": script_context_registry[session_id]["_active_list"],
                "mode": script_mode
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

