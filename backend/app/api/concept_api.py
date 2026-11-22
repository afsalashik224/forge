from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.database.db import db
from app.repositories.concept_repository import _UNSET
from app.services.concept_service import ConceptService

concept_api = Blueprint(
    "concept_api",
    __name__,
    url_prefix="/api/concepts",
)

service = ConceptService()


@concept_api.post("/")
def create_concept():
    if not request.is_json:
        return jsonify({
            "error": "Request must be JSON with Content-Type: application/json.",
            "message": "Request must be JSON with Content-Type: application/json."
        }), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a valid JSON object.",
            "message": "Request body must be a valid JSON object."
        }), 400

    title = data.get("title")
    slug = data.get("slug")
    summary = data.get("summary", "")

    if title is None or slug is None:
        return jsonify({
            "error": "Fields 'title' and 'slug' are required.",
            "message": "Fields 'title' and 'slug' are required."
        }), 400

    if not isinstance(title, str) or not isinstance(slug, str):
        return jsonify({
            "error": "Fields 'title' and 'slug' must be strings.",
            "message": "Fields 'title' and 'slug' must be strings."
        }), 400

    title = title.strip()
    slug = slug.strip()

    if not title:
        return jsonify({
            "error": "Field 'title' cannot be empty.",
            "message": "Field 'title' cannot be empty."
        }), 400

    if not slug:
        return jsonify({
            "error": "Field 'slug' cannot be empty.",
            "message": "Field 'slug' cannot be empty."
        }), 400

    if summary is not None and not isinstance(summary, str):
        return jsonify({
            "error": "Field 'summary' must be a string.",
            "message": "Field 'summary' must be a string."
        }), 400

    summary = summary.strip() if summary else ""

    try:
        concept = service.create_concept(
            title=title,
            slug=slug,
            summary=summary,
        )
    except ValueError as e:
        return jsonify({
            "error": str(e),
            "message": str(e)
        }), 409
    except IntegrityError as e:
        db.session.rollback()
        err_str = str(e).lower()
        if ("unique constraint" in err_str or "unique" in err_str) and ("slug" in err_str):
            return jsonify({
                "error": f"Concept with slug '{slug}' already exists.",
                "message": f"Concept with slug '{slug}' already exists."
            }), 409
        current_app.logger.warning("Database integrity constraint violation on create: %s", e)
        return jsonify({
            "error": "Database integrity constraint violation.",
            "message": "Database integrity constraint violation."
        }), 400
    except Exception as e:
        current_app.logger.exception("Unexpected error while creating concept: %s", e)
        db.session.rollback()
        return jsonify({
            "error": "An unexpected error occurred while creating the concept.",
            "message": "An unexpected error occurred while creating the concept."
        }), 500

    return jsonify({
        "message": "Concept created successfully.",
        "data": {
            "id": concept.id,
            "title": concept.title,
            "slug": concept.slug,
            "summary": concept.summary,
            "status": concept.status,
            "created_at": concept.created_at.isoformat() if concept.created_at else None,
            "updated_at": concept.updated_at.isoformat() if concept.updated_at else None,
        }
    }), 201


@concept_api.get("/")
def get_concepts():
    try:
        concepts = service.get_all_concepts()
        return jsonify([
            {
                "id": concept.id,
                "title": concept.title,
                "slug": concept.slug,
                "summary": concept.summary,
                "status": concept.status,
                "created_at": concept.created_at.isoformat() if concept.created_at else None,
                "updated_at": concept.updated_at.isoformat() if concept.updated_at else None,
            }
            for concept in concepts
        ])
    except Exception as e:
        current_app.logger.exception("Unexpected error while fetching concepts: %s", e)
        return jsonify({
            "error": "An unexpected error occurred while fetching concepts.",
            "message": "An unexpected error occurred while fetching concepts."
        }), 500


@concept_api.get("/<slug>")
def get_concept(slug):
    try:
        concept = service.get_concept_by_slug(slug)
        if concept is None:
            return jsonify({
                "error": "Concept not found.",
                "message": "Concept not found."
            }), 404

        return jsonify({
            "id": concept.id,
            "title": concept.title,
            "slug": concept.slug,
            "summary": concept.summary,
            "status": concept.status,
            "created_at": concept.created_at.isoformat() if concept.created_at else None,
            "updated_at": concept.updated_at.isoformat() if concept.updated_at else None,
        })
    except Exception as e:
        current_app.logger.exception("Unexpected error while retrieving concept: %s", e)
        return jsonify({
            "error": "An unexpected error occurred while retrieving the concept.",
            "message": "An unexpected error occurred while retrieving the concept."
        }), 500


@concept_api.put("/<slug>")
def update_concept(slug):
    if not request.is_json:
        return jsonify({
            "error": "Request must be JSON with Content-Type: application/json.",
            "message": "Request must be JSON with Content-Type: application/json."
        }), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a valid JSON object.",
            "message": "Request body must be a valid JSON object."
        }), 400

    title = data.get("title")
    new_slug = data.get("slug")

    if title is None or new_slug is None:
        return jsonify({
            "error": "Fields 'title' and 'slug' are required.",
            "message": "Fields 'title' and 'slug' are required."
        }), 400

    if not isinstance(title, str) or not isinstance(new_slug, str):
        return jsonify({
            "error": "Fields 'title' and 'slug' must be strings.",
            "message": "Fields 'title' and 'slug' must be strings."
        }), 400

    title = title.strip()
    new_slug = new_slug.strip()

    if not title:
        return jsonify({
            "error": "Field 'title' cannot be empty.",
            "message": "Field 'title' cannot be empty."
        }), 400

    if not new_slug:
        return jsonify({
            "error": "Field 'slug' cannot be empty.",
            "message": "Field 'slug' cannot be empty."
        }), 400

    # Summary: distinguish omitted from explicit null or string
    if "summary" in data:
        raw_summary = data["summary"]
        if raw_summary is not None and not isinstance(raw_summary, str):
            return jsonify({
                "error": "Field 'summary' must be a string or null.",
                "message": "Field 'summary' must be a string or null."
            }), 400
        if raw_summary is None or raw_summary.strip() == "":
            summary = None
        else:
            summary = raw_summary.strip()
    else:
        summary = _UNSET

    # Status: preserve when omitted or null; validate when provided as string
    if "status" in data:
        raw_status = data["status"]
        if raw_status is None:
            status = _UNSET
        elif not isinstance(raw_status, str):
            return jsonify({
                "error": "Field 'status' must be a string.",
                "message": "Field 'status' must be a string."
            }), 400
        else:
            status_str = raw_status.strip().upper()
            if status_str not in {"DRAFT", "PUBLISHED", "ARCHIVED"}:
                return jsonify({
                    "error": "Field 'status' must be one of: DRAFT, PUBLISHED, ARCHIVED.",
                    "message": "Field 'status' must be one of: DRAFT, PUBLISHED, ARCHIVED."
                }), 400
            status = status_str
    else:
        status = _UNSET

    try:
        updated = service.update_concept(
            current_slug=slug,
            title=title,
            slug=new_slug,
            summary=summary,
            status=status,
        )
    except LookupError as e:
        return jsonify({
            "error": str(e),
            "message": str(e)
        }), 404
    except ValueError as e:
        return jsonify({
            "error": str(e),
            "message": str(e)
        }), 409
    except IntegrityError as e:
        db.session.rollback()
        err_str = str(e).lower()
        if ("unique constraint" in err_str or "unique" in err_str) and ("slug" in err_str):
            return jsonify({
                "error": f"Concept with slug '{new_slug}' already exists.",
                "message": f"Concept with slug '{new_slug}' already exists."
            }), 409
        current_app.logger.warning("Database integrity constraint violation on update: %s", e)
        return jsonify({
            "error": "Database integrity constraint violation.",
            "message": "Database integrity constraint violation."
        }), 400
    except Exception as e:
        current_app.logger.exception("Unexpected error while updating concept: %s", e)
        db.session.rollback()
        return jsonify({
            "error": "An unexpected error occurred while updating the concept.",
            "message": "An unexpected error occurred while updating the concept."
        }), 500

    return jsonify({
        "message": "Concept updated successfully.",
        "data": {
            "id": updated.id,
            "title": updated.title,
            "slug": updated.slug,
            "summary": updated.summary,
            "status": updated.status,
            "created_at": updated.created_at.isoformat() if updated.created_at else None,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
    }), 200


@concept_api.delete("/<slug>")
def delete_concept(slug):
    try:
        deleted = service.delete_concept(slug)
    except LookupError as e:
        return jsonify({
            "error": str(e),
            "message": str(e)
        }), 404
    except Exception as e:
        current_app.logger.exception("Unexpected error while deleting concept: %s", e)
        db.session.rollback()
        return jsonify({
            "error": "An unexpected error occurred while deleting the concept.",
            "message": "An unexpected error occurred while deleting the concept."
        }), 500

    return jsonify({
        "message": "Concept deleted successfully.",
        "data": {
            "id": deleted["id"],
            "slug": deleted["slug"]
        }
    }), 200
