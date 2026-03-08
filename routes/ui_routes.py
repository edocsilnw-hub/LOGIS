from flask import Response
import os

def register_ui_routes(app, config):

    AI_CODE_PATH = config["AI_CODE_PATH"]

    @app.route("/")
    def home():
        try:
            path = os.path.join(AI_CODE_PATH, "ui", "AI_Interface.html")

            with open(path, "r", encoding="utf-8") as f:
                html = f.read()

            return Response(html, mimetype="text/html")

        except Exception as e:
            return f"Error loading interface: {e}", 500