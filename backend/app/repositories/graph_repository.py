from sqlalchemy.exc import IntegrityError
from app.database.db import db
from app.models.concept import Concept
from app.models.concept_relationship import ConceptRelationship
from app.models.repository import Repository
from app.models.workspace import Workspace


class GraphRepository:
    """Data access layer for explicit concept relationships and graph snapshots."""

    def create_relationship(self, relationship):
        try:
            db.session.add(relationship)
            db.session.commit()
            return relationship
        except IntegrityError:
            db.session.rollback()
            raise

    def get_relationship_by_id(self, relationship_id):
        return db.session.get(ConceptRelationship, relationship_id)

    def get_relationship(self, source_concept_id, target_concept_id, relationship_type):
        return ConceptRelationship.query.filter_by(
            source_concept_id=source_concept_id,
            target_concept_id=target_concept_id,
            relationship_type=relationship_type,
        ).first()

    def get_all_relationships(self, concept_id=None, relationship_type=None):
        query = ConceptRelationship.query
        if concept_id is not None:
            query = query.filter(
                (ConceptRelationship.source_concept_id == concept_id)
                | (ConceptRelationship.target_concept_id == concept_id)
            )
        if relationship_type:
            query = query.filter_by(relationship_type=relationship_type)
        return query.order_by(ConceptRelationship.id.asc()).all()

    def delete_relationship(self, relationship):
        try:
            db.session.delete(relationship)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise

    def load_graph_entities(self):
        """Fetch all real workspaces, repositories, concepts, and explicit relationships."""
        workspaces = Workspace.query.order_by(Workspace.id.asc()).all()
        repositories = Repository.query.order_by(Repository.id.asc()).all()
        concepts = Concept.query.order_by(Concept.id.asc()).all()
        relationships = ConceptRelationship.query.order_by(ConceptRelationship.id.asc()).all()
        return {
            "workspaces": workspaces,
            "repositories": repositories,
            "concepts": concepts,
            "relationships": relationships,
        }
