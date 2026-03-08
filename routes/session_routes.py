from os import path

from flask import request, jsonify
import os

def register_session_routes(app, config):

    SESSIONS_DIR = config["SESSIONS_DIR"]
    current_session_info = config["current_session_info"]


    @app.route("/create_session", methods=["POST"])
    def create_session():
        data = request.get_json()
        session_id = data.get("session_id")

        if not session_id:
            return jsonify({"error": "No name provided"}), 400
        path = os.path.join(SESSIONS_DIR, f"{session_id}.txt")

        if os.path.exists(path):
            return jsonify({"error": "Session already exists"}), 400
        
        path = os.path.join(SESSIONS_DIR, f"{session_id}.txt")

        with open(path, "w", encoding="utf-8") as f:
            f.write(f"--- SESSION START: {session_id} ---\n")

        current_session_info["id"] = session_id

        return jsonify({"status": "Success"})

    @app.route("/load_session", methods=["POST"])
    def load_session():
        """Missing logic for the 'LOAD' button."""
        data = request.get_json() or {}
        session_id = data.get("session_id")
        path = os.path.join(SESSIONS_DIR, f"{session_id}.txt")
        
        if os.path.exists(path):

            current_session_info["id"] = session_id

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            return jsonify({"status": "Success", "content": content})
        return jsonify({"error": "Session not found"}), 404

    @app.route("/end_session", methods=["POST"])
    def end_session():
        """Missing logic for the 'SAVE' button."""
        return jsonify({"status": "Success"})



