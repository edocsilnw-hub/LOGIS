from flask import Blueprint, request, jsonify
from tools.debug_assistant import debug_error

debug_bp = Blueprint("debug", __name__)


@debug_bp.route("/debug", methods=["POST"])
def debug():
    data = request.json
    error = data.get("error", "")
    context = data.get("context", "")

    result = debug_error(error, context)

    return jsonify({"analysis": result})


def register_debug_routes(app, ctx):
    """
    Called automatically by routes/routes.py
    """
    app.register_blueprint(debug_bp)