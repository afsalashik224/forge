import json

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


def _parse_tags(tags_raw):
    """Parse tags from JSON string to list."""
    if not tags_raw:
        return []
    try:
        parsed = json.loads(tags_raw)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _serialize_concept(concept, detailed=False):
    """Serialize a concept model to a JSON-safe dict."""
    repos = getattr(concept, "repositories", [])
    seen_ws = {}
    for r in repos:
        for w in getattr(r, "workspaces", []):
            if w.id not in seen_ws:
                seen_ws[w.id] = {"id": w.id, "name": w.name, "slug": w.slug}

    payload = {
        "id": concept.id,
        "title": concept.title,
        "slug": concept.slug,
        "summary": concept.summary,
        "content": concept.content or "",
        "status": concept.status,
        "category": concept.category or "",
        "tags": _parse_tags(concept.tags),
        "created_at": concept.created_at.isoformat() if concept.created_at else None,
        "updated_at": concept.updated_at.isoformat() if concept.updated_at else None,
        "repositories_count": len(repos),
        "repositories": [
            {
                "id": r.id,
                "name": r.name,
                "slug": r.slug,
                "primary_language": r.primary_language,
                "status": r.status,
            }
            for r in repos
        ],
        "workspaces": list(seen_ws.values()),
    }
    if detailed:
        payload["content"] = concept.content or ""
    return payload


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
    content = data.get("content", "")
    tags = data.get("tags", [])
    category = data.get("category", "")
    repository_ids = data.get("repository_ids", [])

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

    if content is not None and not isinstance(content, str):
        return jsonify({
            "error": "Field 'content' must be a string.",
            "message": "Field 'content' must be a string."
        }), 400

    if tags is not None and not isinstance(tags, list):
        return jsonify({
            "error": "Field 'tags' must be a list of strings.",
            "message": "Field 'tags' must be a list of strings."
        }), 400

    if category is not None and not isinstance(category, str):
        return jsonify({
            "error": "Field 'category' must be a string.",
            "message": "Field 'category' must be a string."
        }), 400

    if repository_ids is not None and not isinstance(repository_ids, list):
        return jsonify({
            "error": "Field 'repository_ids' must be a list of integers.",
            "message": "Field 'repository_ids' must be a list of integers."
        }), 400

    # Clean tags
    if tags:
        tags = [t.strip() for t in tags if isinstance(t, str) and t.strip()]

    try:
        concept = service.create_concept(
            title=title,
            slug=slug,
            summary=summary,
            content=content or "",
            tags=tags or [],
            category=(category or "").strip(),
            repository_ids=repository_ids,
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
        "data": _serialize_concept(concept, detailed=True),
    }), 201


@concept_api.get("/")
def get_concepts():
    try:
        # Check for search query parameters
        q = request.args.get("q", "").strip()
        tags_param = request.args.get("tags", "").strip()
        category_param = request.args.get("category", "").strip()
        status_param = request.args.get("status", "").strip()
        repository_param = request.args.get("repository", "").strip()
        workspace_param = request.args.get("workspace", "").strip()

        if q or tags_param or category_param or status_param or repository_param or workspace_param:
            search_tags = [t.strip() for t in tags_param.split(",") if t.strip()] if tags_param else None
            concepts = service.search_concepts(
                query=q or None,
                tags=search_tags,
                category=category_param or None,
                status=status_param or None,
                repository_slug=repository_param or None,
                workspace_slug=workspace_param or None,
            )
        else:
            concepts = service.get_all_concepts()

        return jsonify([_serialize_concept(c) for c in concepts])
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

        return jsonify(_serialize_concept(concept, detailed=True))
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

    # Content: distinguish omitted from provided
    if "content" in data:
        raw_content = data["content"]
        if raw_content is not None and not isinstance(raw_content, str):
            return jsonify({
                "error": "Field 'content' must be a string or null.",
                "message": "Field 'content' must be a string or null."
            }), 400
        content = raw_content if raw_content else ""
    else:
        content = _UNSET

    # Tags: distinguish omitted from provided
    if "tags" in data:
        raw_tags = data["tags"]
        if raw_tags is None:
            tags = []
        elif not isinstance(raw_tags, list):
            return jsonify({
                "error": "Field 'tags' must be a list of strings or null.",
                "message": "Field 'tags' must be a list of strings or null."
            }), 400
        else:
            tags = [t.strip() for t in raw_tags if isinstance(t, str) and t.strip()]
    else:
        tags = _UNSET

    # Category: distinguish omitted from provided
    if "category" in data:
        raw_category = data["category"]
        if raw_category is not None and not isinstance(raw_category, str):
            return jsonify({
                "error": "Field 'category' must be a string or null.",
                "message": "Field 'category' must be a string or null."
            }), 400
        category = (raw_category or "").strip()
    else:
        category = _UNSET

    # Repository associations: distinguish omitted from provided
    if "repository_ids" in data:
        raw_repo_ids = data["repository_ids"]
        if raw_repo_ids is None:
            repository_ids = []
        elif not isinstance(raw_repo_ids, list):
            return jsonify({
                "error": "Field 'repository_ids' must be a list of integers or null.",
                "message": "Field 'repository_ids' must be a list of integers or null."
            }), 400
        else:
            repository_ids = raw_repo_ids
    else:
        repository_ids = _UNSET

    try:
        updated = service.update_concept(
            current_slug=slug,
            title=title,
            slug=new_slug,
            summary=summary,
            status=status,
            content=content,
            tags=tags,
            category=category,
            repository_ids=repository_ids,
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
        "data": _serialize_concept(updated, detailed=True),
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
