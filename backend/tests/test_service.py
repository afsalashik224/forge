from app import create_app
import app.models

from app.services.concept_service import ConceptService

app = create_app()

with app.app_context():

    service = ConceptService()

    concept = service.create_concept(
        title="REST API",
        slug="rest-api",
        summary="An architectural style for designing networked applications."
    )

    print(concept)
