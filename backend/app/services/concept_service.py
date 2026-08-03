from app.models.concept import Concept
from app.repositories.concept_repository import ConceptRepository


class ConceptService:

    def __init__(self, repository=None):
        self.repository = repository or ConceptRepository()

    def create_concept(self, title, slug, summary):

        existing = self.repository.get_by_slug(slug)

        if existing:
            raise ValueError(
                f"Concept with slug '{slug}' already exists."
            )

        concept = Concept(
            title=title,
            slug=slug,
            summary=summary,
        )

        return self.repository.create(concept)

    def get_all_concepts(self):
        return self.repository.get_all()


    def get_concept_by_slug(self, slug):
        return self.repository.get_by_slug(slug)
