from flask import jsonify


def register_debug_routes(app, ctx):

    @app.route("/debug/routes", methods=["GET"])
    def debug_routes():

        routes = []

        for rule in app.url_map.iter_rules():
            routes.append({
                "endpoint": rule.endpoint,
                "methods": list(rule.methods),
                "path": str(rule)
            })

        return jsonify({
            "status": "ok",
            "routes": routes
        })