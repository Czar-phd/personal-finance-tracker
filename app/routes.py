from flask import Blueprint, jsonify

bp = Blueprint("main", __name__)

@bp.get("/")
def index():
    return jsonify({"status": "ok", "app": "personal-finance-tracker"})

@bp.get("/favicon.ico")
def favicon():
    from flask import current_app, send_from_directory
    return send_from_directory(current_app.root_path + "/static", "favicon.ico")
