from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.database.db import db
from app.models.concept_relationship import ALLOWED_RELATIONSHIP_TYPES
from app.services.graph_service import DuplicateRelationshipError, GraphService

graph_api = Blueprint(
    "graph_api",
    __name__,
    url_prefix="/api/graph",
)

service = GraphService()


@graph_api.get("/")
def get_graph():
    try:
        entity_types_param = request.args.get("entity_types", "").strip()
        rel_types_param = request.args.get("relationship_types", "").strip()
        workspace = request.args.get("workspace", "").strip() or None
        repository = request.args.get("repository", "").strip() or None
        category = request.args.get("category", "").strip() or None
        status = request.args.get("status", "").strip() or None
        query = request.args.get("q", "").strip() or None
        focus = request.args.get("focus", "").strip() or None
        include_neighbors = request.args.get("include_neighbors", "").lower() in {"1", "true", "yes"}

        depth_raw = request.args.get("depth", "1")
        try:
            depth = int(depth_raw)
        except ValueError:
            return jsonify({
                "error": "Parameter 'depth' must be an integer.",
                "message": "Parameter 'depth' must be an integer.",
            }), 400

        entity_types = [t.strip() for t in entity_types_param.split(",") if t.strip()] if entity_types_param else None
        rel_types = [t.strip() for t in rel_types_param.split(",") if t.strip()] if rel_types_param else None

        graph_data = service.build_graph(
            entity_types=entity_types,
            relationship_types=rel_types,
            workspace_slug=workspace,
            repository_slug=repository,
            category=category,
            status=status,
            query=query,
            focus_node_id=focus,
            depth=depth,
            include_neighbors=include_neighbors,
        )
        return jsonify(graph_data), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404
    except Exception as exc:
        current_app.logger.exception("Unexpected error building knowledge graph: %s", exc)
        return jsonify({
            "error": "Failed to build knowledge graph.",
            "message": str(exc),
        }), 500


@graph_api.get("/nodes/<entity_type>/<identifier>/neighbors")
def explore_node_neighbors(entity_type, identifier):
    etype = entity_type.strip().lower()
    if etype not in {"workspace", "repository", "concept"}:
        return jsonify({
            "error": "Entity type must be one of: workspace, repository, concept.",
            "message": "Entity type must be one of: workspace, repository, concept.",
        }), 400

    depth_raw = request.args.get("depth", "1")
    try:
        depth = int(depth_raw)
    except ValueError:
        return jsonify({
            "error": "Parameter 'depth' must be an integer.",
            "message": "Parameter 'depth' must be an integer.",
        }), 400

    try:
        exploration = service.explore_node(etype, identifier, depth=depth)
        return jsonify(exploration), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404
    except Exception as exc:
        current_app.logger.exception("Unexpected error exploring graph node: %s", exc)
        return jsonify({
            "error": "Failed to explore graph node.",
            "message": str(exc),
        }), 500


@graph_api.get("/relationships")
def get_relationships():
    try:
        concept_slug = request.args.get("concept", "").strip() or None
        rel_type = request.args.get("relationship_type", "").strip() or None
        rels = service.list_relationships(
            concept_slug=concept_slug,
            relationship_type=rel_type,
        )
        return jsonify({
            "relationships": [service.serialize_relationship(r) for r in rels],
            "allowed_types": list(ALLOWED_RELATIONSHIP_TYPES),
        }), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404
    except ValueError as ve:
        return jsonify({"error": str(ve), "message": str(ve)}), 400
    except Exception as exc:
        current_app.logger.exception("Unexpected error listing relationships: %s", exc)
        return jsonify({
            "error": "Failed to list relationships.",
            "message": str(exc),
        }), 500


@graph_api.post("/relationships")
def create_relationship():
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

    source_id = data.get("source_concept_id")
    target_id = data.get("target_concept_id")
    source_slug = data.get("source_slug")
    target_slug = data.get("target_slug")
    rel_type = data.get("relationship_type")
    description = data.get("description")

    if source_id is None and not source_slug:
        return jsonify({
            "error": "Either 'source_concept_id' or 'source_slug' is required.",
            "message": "Either 'source_concept_id' or 'source_slug' is required.",
        }), 400

    if target_id is None and not target_slug:
        return jsonify({
            "error": "Either 'target_concept_id' or 'target_slug' is required.",
            "message": "Either 'target_concept_id' or 'target_slug' is required.",
        }), 400

    if not rel_type or not isinstance(rel_type, str):
        return jsonify({
            "error": "Field 'relationship_type' is required and must be a string.",
            "message": "Field 'relationship_type' is required and must be a string.",
        }), 400

    if description is not None and not isinstance(description, str):
        return jsonify({
            "error": "Field 'description' must be a string or null.",
            "message": "Field 'description' must be a string or null.",
        }), 400

    try:
        rel = service.create_relationship(
            source_concept_id=source_id,
            target_concept_id=target_id,
            source_slug=source_slug,
            target_slug=target_slug,
            relationship_type=rel_type,
            description=description,
        )
        return jsonify({
            "message": "Relationship created successfully.",
            "data": service.serialize_relationship(rel),
        }), 201
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404
    except DuplicateRelationshipError as dre:
        return jsonify({"error": str(dre), "message": str(dre)}), 409
    except ValueError as ve:
        return jsonify({"error": str(ve), "message": str(ve)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Duplicate or invalid relationship edge.",
            "message": "Duplicate or invalid relationship edge.",
        }), 409
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Unexpected error creating relationship: %s", exc)
        return jsonify({
            "error": "Failed to create relationship.",
            "message": str(exc),
        }), 500


@graph_api.delete("/relationships/<int:relationship_id>")
def delete_relationship(relationship_id):
    try:
        deleted = service.delete_relationship(relationship_id)
        return jsonify({
            "message": "Relationship deleted successfully.",
            "data": deleted,
        }), 200
    except LookupError as le:
        return jsonify({"error": str(le), "message": str(le)}), 404
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Unexpected error deleting relationship: %s", exc)
        return jsonify({
            "error": "Failed to delete relationship.",
            "message": str(exc),
        }), 500
