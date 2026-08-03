from flask import Blueprint, jsonify, request

from app.services.concept_service import ConceptService

concept_api = Blueprint(
	"concept_api",
	__name__,
	url_prefix="/api/concepts",
)


service = ConceptService()

@concept_api.post("/")
def create_concept():

	data = request.get_json()

	concept = service.create_concept(
		title=data["title"],
		slug=data["slug"],
		summary=data["summary"]
	)

	return jsonify({
	      "message":"Concept created successfully.",
	      "data": {
		"id": concept.id,
		"title": concept.title,
		"slug": concept.slug,
		"summary": concept.summary,
		"status": concept.status,
	      }
	}),201

@concept_api.get("/")
def get_concepts():

    concepts = service.get_all_concepts()

    return jsonify([
        {
            "id": concept.id,
            "title": concept.title,
            "slug": concept.slug,
            "summary": concept.summary,
            "status": concept.status,
        }
        for concept in concepts
    ])

@concept_api.get("/<slug>")
def get_concept(slug):

    concept = service.get_concept_by_slug(slug)

    if concept is None:
        return jsonify({
            "message": "Concept not found."
        }), 404

    return jsonify({
        "id": concept.id,
        "title": concept.title,
        "slug": concept.slug,
        "summary": concept.summary,
        "status": concept.status,
    })
