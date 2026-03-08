from flask import jsonify, request
import os

def register_memory_routes(app, config):

    CHUNKBLOCKS_DIR = config["CHUNKBLOCKS_DIR"]
    active_chunk_selection = config["active_chunk_selection"]
    summarize_chunk_content = config["summarize_chunk_content"]

    @app.route("/list_chunks", methods=["GET"])
    def list_chunks():
        try:
            files = [
                f for f in os.listdir(CHUNKBLOCKS_DIR)
                if f.startswith("CHUNK_") and f.endswith(".txt")
            ]

            return jsonify({"chunks": sorted(files)})

        except Exception as e:
            print("[CHUNK LIST ERROR]", e)
            return jsonify({"chunks": []})


    @app.route("/set_chunk", methods=["POST"])
    def set_chunk():

        data = request.get_json() or {}
        session_id = data.get("session_id")
        chunk_name = data.get("chunk_name")

        if not session_id:
            return jsonify({"error": "No session_id provided"}), 400

        # Prevent invalid chunk names
        if chunk_name and not chunk_name.startswith("CHUNK_"):
            return jsonify({"error": "Invalid chunk name"}), 400

        active_chunk_selection[session_id] = {
            "name": chunk_name,
            "summary": None
        }

        if chunk_name:

            chunk_path = os.path.join(CHUNKBLOCKS_DIR, chunk_name)

            if os.path.exists(chunk_path):

                with open(chunk_path, "r", encoding="utf-8") as f:
                    full_content = f.read()

                summary = summarize_chunk_content(chunk_name, full_content)

                active_chunk_selection[session_id]["summary"] = summary

        return jsonify({"status": "Success"}) 