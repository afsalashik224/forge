from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.database.db import db
from app.repositories.repository_repository import _UNSET
from app.services.repository_service import RepositoryService

repository_api = Blueprint(
    "repository_api",
    __name__,
    url_prefix="/api/repositories",
)

service = RepositoryService()


def serialize_repository(repo, detailed=False):
    payload = {
        "id": repo.id,
        "name": repo.name,
        "slug": repo.slug,
        "description": repo.description,
        "vcs_url": repo.vcs_url,
        "primary_language": repo.primary_language,
        "status": repo.status,
        "workspaces_count": len(repo.workspaces),
        "concepts_count": len(repo.concepts),
        "created_at": repo.created_at.isoformat() if repo.created_at else None,
        "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
    }
    if detailed:
        payload["workspaces"] = [
            {"id": w.id, "name": w.name, "slug": w.slug}
            for w in repo.workspaces
        ]
        payload["concepts"] = [
            {
                "id": c.id,
                "title": c.title,
                "slug": c.slug,
                "status": c.status,
                "summary": c.summary,
            }
            for c in repo.concepts
        ]
    else:
        payload["workspaces"] = [
            {"id": w.id, "name": w.name, "slug": w.slug}
            for w in repo.workspaces
        ]
        payload["concepts"] = [
            {"id": c.id, "title": c.title, "slug": c.slug}
            for c in repo.concepts
        ]
    return payload


@repository_api.get("/")
def get_repositories():
    repositories = service.get_all_repositories()
    return jsonify([serialize_repository(r) for r in repositories]), 200


@repository_api.get("/<slug>")
def get_repository_by_slug(slug):
    repo = service.get_repository_by_slug(slug)
    if not repo:
        return jsonify({
            "error": f"Repository with slug '{slug}' not found.",
            "message": f"Repository with slug '{slug}' not found."
        }), 404
    return jsonify(serialize_repository(repo, detailed=True)), 200


@repository_api.post("/")
def create_repository():
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

    name = data.get("name")
    slug = data.get("slug")
    description = data.get("description", "")
    vcs_url = data.get("vcs_url", "")
    primary_language = data.get("primary_language", "")
    status = data.get("status", "ACTIVE")
    workspace_ids = data.get("workspace_ids", [])
    concept_ids = data.get("concept_ids", [])

    if name is None or slug is None:
        return jsonify({
            "error": "Fields 'name' and 'slug' are required.",
            "message": "Fields 'name' and 'slug' are required."
        }), 400

    if not isinstance(name, str) or not isinstance(slug, str):
        return jsonify({
            "error": "Fields 'name' and 'slug' must be strings.",
            "message": "Fields 'name' and 'slug' must be strings."
        }), 400

    name = name.strip()
    slug = slug.strip()

    if not name:
        return jsonify({
            "error": "Field 'name' cannot be empty.",
            "message": "Field 'name' cannot be empty."
        }), 400

    if not slug:
        return jsonify({
            "error": "Field 'slug' cannot be empty.",
            "message": "Field 'slug' cannot be empty."
        }), 400

    if description is not None and not isinstance(description, str):
        return jsonify({
            "error": "Field 'description' must be a string or null.",
            "message": "Field 'description' must be a string or null."
        }), 400
    if description:
        description = description.strip()

    if vcs_url is not None and not isinstance(vcs_url, str):
        return jsonify({
            "error": "Field 'vcs_url' must be a string or null.",
            "message": "Field 'vcs_url' must be a string or null."
        }), 400
    if vcs_url:
        vcs_url = vcs_url.strip()

    if primary_language is not None and not isinstance(primary_language, str):
        return jsonify({
            "error": "Field 'primary_language' must be a string or null.",
            "message": "Field 'primary_language' must be a string or null."
        }), 400
    if primary_language:
        primary_language = primary_language.strip()

    if status and status not in ("ACTIVE", "ARCHIVED", "MAINTENANCE"):
        return jsonify({
            "error": "Field 'status' must be 'ACTIVE', 'ARCHIVED', or 'MAINTENANCE'.",
            "message": "Field 'status' must be 'ACTIVE', 'ARCHIVED', or 'MAINTENANCE'."
        }), 400

    if workspace_ids is not None and not isinstance(workspace_ids, list):
        return jsonify({
            "error": "Field 'workspace_ids' must be a list of integers.",
            "message": "Field 'workspace_ids' must be a list of integers."
        }), 400

    if concept_ids is not None and not isinstance(concept_ids, list):
        return jsonify({
            "error": "Field 'concept_ids' must be a list of integers.",
            "message": "Field 'concept_ids' must be a list of integers."
        }), 400

    try:
        repo = service.create_repository(
            name=name,
            slug=slug,
            description=description,
            vcs_url=vcs_url,
            primary_language=primary_language,
            status=status or "ACTIVE",
            workspace_ids=workspace_ids,
            concept_ids=concept_ids,
        )
        return jsonify({
            "message": "Repository created successfully.",
            "data": serialize_repository(repo, detailed=True),
        }), 201
    except ValueError as ve:
        return jsonify({"error": str(ve), "message": str(ve)}), 409
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": f"Repository with slug '{slug}' already exists.",
            "message": f"Repository with slug '{slug}' already exists."
        }), 409
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Unexpected error while creating repository")
        return jsonify({
            "error": "Failed to create repository due to internal server error.",
            "message": str(exc)
        }), 500


@repository_api.put("/<slug>")
def update_repository(slug):
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

    name = data.get("name", _UNSET)
    new_slug = data.get("slug", _UNSET)
    description = data.get("description", _UNSET)
    vcs_url = data.get("vcs_url", _UNSET)
    primary_language = data.get("primary_language", _UNSET)
    status = data.get("status", _UNSET)
    workspace_ids = data.get("workspace_ids", _UNSET)
    concept_ids = data.get("concept_ids", _UNSET)

    if name is not _UNSET:
        if not isinstance(name, str) or not name.strip():
            return jsonify({
                "error": "Field 'name' must be a non-empty string.",
                "message": "Field 'name' must be a non-empty string."
            }), 400
        name = name.strip()

    if new_slug is not _UNSET:
        if not isinstance(new_slug, str) or not new_slug.strip():
            return jsonify({
                "error": "Field 'slug' must be a non-empty string.",
                "message": "Field 'slug' must be a non-empty string."
            }), 400
        new_slug = new_slug.strip()

    if description is not _UNSET and description is not None:
        if not isinstance(description, str):
            return jsonify({
                "error": "Field 'description' must be a string or null.",
                "message": "Field 'description' must be a string or null."
            }), 400
        description = description.strip()

    if vcs_url is not _UNSET and vcs_url is not None:
        if not isinstance(vcs_url, str):
            return jsonify({
                "error": "Field 'vcs_url' must be a string or null.",
                "message": "Field 'vcs_url' must be a string or null."
            }), 400
        vcs_url = vcs_url.strip()

    if primary_language is not _UNSET and primary_language is not None:
        if not isinstance(primary_language, str):
            return jsonify({
                "error": "Field 'primary_language' must be a string or null.",
                "message": "Field 'primary_language' must be a string or null."
            }), 400
        primary_language = primary_language.strip()

    if status is not _UNSET:
        if status not in ("ACTIVE", "ARCHIVED", "MAINTENANCE"):
            return jsonify({
                "error": "Field 'status' must be 'ACTIVE', 'ARCHIVED', or 'MAINTENANCE'.",
                "message": "Field 'status' must be 'ACTIVE', 'ARCHIVED', or 'MAINTENANCE'."
            }), 400

    if workspace_ids is not _UNSET and workspace_ids is not None:
        if not isinstance(workspace_ids, list):
            return jsonify({
                "error": "Field 'workspace_ids' must be a list of integers.",
                "message": "Field 'workspace_ids' must be a list of integers."
            }), 400

    if concept_ids is not _UNSET and concept_ids is not None:
        if not isinstance(concept_ids, list):
            return jsonify({
                "error": "Field 'concept_ids' must be a list of integers.",
                "message": "Field 'concept_ids' must be a list of integers."
            }), 400

    try:
        updated = service.update_repository(
            current_slug=slug,
            name=name,
            slug=new_slug,
            description=description,
            vcs_url=vcs_url,
            primary_language=primary_language,
            status=status,
            workspace_ids=workspace_ids,
            concept_ids=concept_ids,
        )
        return jsonify({
            "message": "Repository updated successfully.",
            "data": serialize_repository(updated, detailed=True),
        }), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404
    except ValueError as ve:
        return jsonify({"error": str(ve), "message": str(ve)}), 409
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Integrity conflict occurred while updating repository.",
            "message": "Repository with the requested slug already exists."
        }), 409
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Unexpected error while updating repository")
        return jsonify({
            "error": "Failed to update repository due to internal server error.",
            "message": str(exc)
        }), 500


@repository_api.delete("/<slug>")
def delete_repository(slug):
    try:
        result = service.delete_repository(slug)
        return jsonify({
            "message": f"Repository '{result['name']}' deleted successfully.",
            "data": result,
        }), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Unexpected error while deleting repository")
        return jsonify({
            "error": "Failed to delete repository due to internal server error.",
            "message": str(exc)
        }), 500


@repository_api.post("/<slug>/concepts")
def link_concept(slug):
    if not request.is_json:
        return jsonify({"error": "Request must be JSON.", "message": "Request must be JSON."}), 400

    data = request.get_json(silent=True) or {}
    concept_slug = data.get("concept_slug")
    if not concept_slug or not isinstance(concept_slug, str):
        return jsonify({
            "error": "Field 'concept_slug' is required.",
            "message": "Field 'concept_slug' is required."
        }), 400

    try:
        repo = service.add_concept_to_repository(slug, concept_slug.strip())
        return jsonify({
            "message": f"Concept '{concept_slug}' linked to repository '{slug}'.",
            "data": serialize_repository(repo, detailed=True),
        }), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404


@repository_api.delete("/<slug>/concepts/<concept_slug>")
def unlink_concept(slug, concept_slug):
    try:
        repo = service.remove_concept_from_repository(slug, concept_slug)
        return jsonify({
            "message": f"Concept '{concept_slug}' unlinked from repository '{slug}'.",
            "data": serialize_repository(repo, detailed=True),
        }), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404
