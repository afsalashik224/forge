from flask import Blueprint, current_app, jsonify, request

from app.services.compass_service import CompassService

compass_api = Blueprint(
    "compass_api",
    __name__,
    url_prefix="/api/compass",
)

service = CompassService()


@compass_api.get("/")
@compass_api.get("/recommendations")
def get_recommendations():
    try:
        refresh_param = request.args.get("refresh", "true").strip().lower()
        refresh = refresh_param not in {"0", "false", "no"}

        status = request.args.get("status", "").strip() or None
        priority = request.args.get("priority", "").strip() or None
        category = request.args.get("category", "").strip() or None
        repository_slug = request.args.get("repository", "").strip() or None

        payload = service.get_recommendations(
            refresh=refresh,
            status=status,
            priority=priority,
            category=category,
            repository_slug=repository_slug,
        )
        return jsonify(payload), 200
    except ValueError as ve:
        return jsonify({"error": str(ve), "message": str(ve)}), 400
    except Exception as exc:
        current_app.logger.exception("Unexpected error loading Forge Compass recommendations: %s", exc)
        return jsonify({
            "error": "Failed to load Forge Compass recommendations.",
            "message": str(exc),
        }), 500


@compass_api.post("/refresh")
def refresh_recommendations():
    try:
        payload = service.get_recommendations(refresh=True)
        return jsonify({
            "message": "Forge Compass recommendations synchronized.",
            **payload,
        }), 200
    except Exception as exc:
        current_app.logger.exception("Unexpected error refreshing recommendations: %s", exc)
        return jsonify({
            "error": "Failed to refresh Forge Compass recommendations.",
            "message": str(exc),
        }), 500


@compass_api.patch("/recommendations/<int:rec_id>")
@compass_api.post("/recommendations/<int:rec_id>/status")
def update_recommendation_status(rec_id):
    if not request.is_json:
        return jsonify({
            "error": "Request must be JSON with Content-Type: application/json.",
            "message": "Request must be JSON with Content-Type: application/json.",
        }), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a valid JSON object.",
            "message": "Request body must be a valid JSON object.",
        }), 400

    status = data.get("status")
    try:
        updated = service.update_recommendation_status(rec_id, status)
        return jsonify({
            "message": f"Recommendation marked as {updated['status']}.",
            "data": updated,
        }), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404
    except ValueError as ve:
        return jsonify({"error": str(ve), "message": str(ve)}), 400
    except Exception as exc:
        current_app.logger.exception("Unexpected error updating recommendation %s: %s", rec_id, exc)
        return jsonify({
            "error": "Failed to update recommendation status.",
            "message": str(exc),
        }), 500
