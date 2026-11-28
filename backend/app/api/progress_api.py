from flask import Blueprint, current_app, jsonify

from app.services.progress_service import ProgressService

progress_api = Blueprint(
    "progress_api",
    __name__,
    url_prefix="/api/progress",
)

service = ProgressService()


@progress_api.get("/")
def get_progress_overview():
    try:
        overview = service.get_progress_overview()
        return jsonify(overview), 200
    except Exception as exc:
        current_app.logger.exception("Unexpected error computing progress overview: %s", exc)
        return jsonify({
            "error": "Failed to compute repository progress.",
            "message": str(exc),
        }), 500


@progress_api.get("/repositories/<slug>")
def get_repository_progress(slug):
    try:
        detail = service.get_repository_progress(slug)
        return jsonify(detail), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404
    except Exception as exc:
        current_app.logger.exception("Unexpected error computing repository progress for '%s': %s", slug, exc)
        return jsonify({
            "error": "Failed to compute repository progress.",
            "message": str(exc),
        }), 500
