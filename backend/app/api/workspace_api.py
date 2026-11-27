from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.database.db import db
from app.repositories.workspace_repository import _UNSET
from app.services.workspace_service import WorkspaceService

workspace_api = Blueprint(
    "workspace_api",
    __name__,
    url_prefix="/api/workspaces",
)

service = WorkspaceService()


def serialize_workspace(ws, detailed=False):
    payload = {
        "id": ws.id,
        "name": ws.name,
        "slug": ws.slug,
        "description": ws.description,
        "repositories_count": len(ws.repositories),
        "created_at": ws.created_at.isoformat() if ws.created_at else None,
        "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
    }
    if detailed:
        payload["repositories"] = [
            {
                "id": r.id,
                "name": r.name,
                "slug": r.slug,
                "description": r.description,
                "primary_language": r.primary_language,
                "status": r.status,
                "concepts_count": len(r.concepts),
            }
            for r in ws.repositories
        ]
    else:
        payload["repositories"] = [
            {"id": r.id, "name": r.name, "slug": r.slug}
            for r in ws.repositories
        ]
    return payload


@workspace_api.get("/")
def get_workspaces():
    workspaces = service.get_all_workspaces()
    return jsonify([serialize_workspace(w) for w in workspaces]), 200


@workspace_api.get("/<slug>")
def get_workspace_by_slug(slug):
    ws = service.get_workspace_by_slug(slug)
    if not ws:
        return jsonify({
            "error": f"Workspace with slug '{slug}' not found.",
            "message": f"Workspace with slug '{slug}' not found."
        }), 404
    return jsonify(serialize_workspace(ws, detailed=True)), 200


@workspace_api.post("/")
def create_workspace():
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
    repository_ids = data.get("repository_ids", [])

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

    if repository_ids is not None and not isinstance(repository_ids, list):
        return jsonify({
            "error": "Field 'repository_ids' must be a list of integers.",
            "message": "Field 'repository_ids' must be a list of integers."
        }), 400

    try:
        ws = service.create_workspace(
            name=name,
            slug=slug,
            description=description,
            repository_ids=repository_ids,
        )
        return jsonify({
            "message": "Workspace created successfully.",
            "data": serialize_workspace(ws, detailed=True),
        }), 201
    except ValueError as ve:
        return jsonify({"error": str(ve), "message": str(ve)}), 409
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": f"Workspace with slug '{slug}' already exists.",
            "message": f"Workspace with slug '{slug}' already exists."
        }), 409
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Unexpected error while creating workspace")
        return jsonify({
            "error": "Failed to create workspace due to internal server error.",
            "message": str(exc)
        }), 500


@workspace_api.put("/<slug>")
def update_workspace(slug):
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
    repository_ids = data.get("repository_ids", _UNSET)

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

    if repository_ids is not _UNSET and repository_ids is not None:
        if not isinstance(repository_ids, list):
            return jsonify({
                "error": "Field 'repository_ids' must be a list of integers.",
                "message": "Field 'repository_ids' must be a list of integers."
            }), 400

    try:
        updated = service.update_workspace(
            current_slug=slug,
            name=name,
            slug=new_slug,
            description=description,
            repository_ids=repository_ids,
        )
        return jsonify({
            "message": "Workspace updated successfully.",
            "data": serialize_workspace(updated, detailed=True),
        }), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404
    except ValueError as ve:
        return jsonify({"error": str(ve), "message": str(ve)}), 409
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Integrity conflict occurred while updating workspace.",
            "message": "Workspace with the requested slug already exists."
        }), 409
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Unexpected error while updating workspace")
        return jsonify({
            "error": "Failed to update workspace due to internal server error.",
            "message": str(exc)
        }), 500


@workspace_api.delete("/<slug>")
def delete_workspace(slug):
    try:
        result = service.delete_workspace(slug)
        return jsonify({
            "message": f"Workspace '{result['name']}' deleted successfully.",
            "data": result,
        }), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Unexpected error while deleting workspace")
        return jsonify({
            "error": "Failed to delete workspace due to internal server error.",
            "message": str(exc)
        }), 500


@workspace_api.post("/<slug>/repositories")
def link_repository(slug):
    if not request.is_json:
        return jsonify({"error": "Request must be JSON.", "message": "Request must be JSON."}), 400

    data = request.get_json(silent=True) or {}
    repo_slug = data.get("repository_slug")
    if not repo_slug or not isinstance(repo_slug, str):
        return jsonify({
            "error": "Field 'repository_slug' is required.",
            "message": "Field 'repository_slug' is required."
        }), 400

    try:
        ws = service.add_repository_to_workspace(slug, repo_slug.strip())
        return jsonify({
            "message": f"Repository '{repo_slug}' linked to workspace '{slug}'.",
            "data": serialize_workspace(ws, detailed=True),
        }), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404


@workspace_api.delete("/<slug>/repositories/<repo_slug>")
def unlink_repository(slug, repo_slug):
    try:
        ws = service.remove_repository_from_workspace(slug, repo_slug)
        return jsonify({
            "message": f"Repository '{repo_slug}' unlinked from workspace '{slug}'.",
            "data": serialize_workspace(ws, detailed=True),
        }), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404
