from app.models.concept import Concept
from app.repositories.concept_repository import ConceptRepository, _UNSET


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

    def update_concept(self, current_slug, title=_UNSET, slug=_UNSET, summary=_UNSET, status=_UNSET):
        concept = self.repository.get_by_slug(current_slug)
        if not concept:
            raise LookupError(f"Concept with slug '{current_slug}' not found.")

        if slug is not _UNSET and slug != current_slug:
            existing = self.repository.get_by_slug(slug)
            if existing:
                raise ValueError(f"Concept with slug '{slug}' already exists.")

        return self.repository.update(
            concept,
            title=title,
            slug=slug,
            summary=summary,
            status=status,
        )

    def delete_concept(self, slug):
        concept = self.repository.get_by_slug(slug)
        if not concept:
            raise LookupError(f"Concept with slug '{slug}' not found.")

        concept_id = concept.id
        self.repository.delete(concept)
        return {"id": concept_id, "slug": slug, "title": concept.title}
