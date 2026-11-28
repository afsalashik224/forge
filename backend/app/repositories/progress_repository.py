from sqlalchemy.orm import selectinload

from app.models.concept import Concept
from app.models.concept_relationship import ConceptRelationship
from app.models.repository import Repository
from app.models.workspace import Workspace


class ProgressRepository:
    """Eager-loading data access for the Progress Engine (avoids N+1 queries)."""

    def load_snapshot(self):
        """Fetch workspaces, repositories, concepts, and graph relationships in constant queries."""
        workspaces = (
            Workspace.query.options(selectinload(Workspace.repositories))
            .order_by(Workspace.name.asc())
            .all()
        )
        repositories = (
            Repository.query.options(
                selectinload(Repository.workspaces),
                selectinload(Repository.concepts),
            )
            .order_by(Repository.name.asc())
            .all()
        )
        concepts = (
            Concept.query.options(
                selectinload(Concept.repositories),
                selectinload(Concept.outgoing_relationships),
                selectinload(Concept.incoming_relationships),
            )
            .order_by(Concept.id.asc())
            .all()
        )
        relationships = ConceptRelationship.query.order_by(ConceptRelationship.id.asc()).all()
        return {
            "workspaces": workspaces,
            "repositories": repositories,
            "concepts": concepts,
            "relationships": relationships,
        }
