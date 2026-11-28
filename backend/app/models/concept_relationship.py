from app.database.db import db

ALLOWED_RELATIONSHIP_TYPES = (
    "DEPENDS_ON",
    "RELATES_TO",
    "IMPLEMENTS",
    "EXTENDS",
    "ALTERNATIVE_TO",
    "SUPERSEDES",
    "PART_OF",
)


class ConceptRelationship(db.Model):
    """Typed directed relationship between two Concept nodes in the Knowledge Graph."""

    __tablename__ = "concept_relationships"
    __table_args__ = (
        db.CheckConstraint(
            "source_concept_id != target_concept_id",
            name="ck_concept_rel_no_self_loop",
        ),
        db.UniqueConstraint(
            "source_concept_id",
            "target_concept_id",
            "relationship_type",
            name="uq_concept_rel_edge",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    source_concept_id = db.Column(
        db.Integer,
        db.ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_concept_id = db.Column(
        db.Integer,
        db.ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type = db.Column(db.String(40), nullable=False)
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=True,
    )

    source_concept = db.relationship(
        "Concept",
        foreign_keys=[source_concept_id],
        back_populates="outgoing_relationships",
    )
    target_concept = db.relationship(
        "Concept",
        foreign_keys=[target_concept_id],
        back_populates="incoming_relationships",
    )

    def __repr__(self):
        return (
            f"<ConceptRelationship {self.source_concept_id} "
            f"-[{self.relationship_type}]-> {self.target_concept_id}>"
        )
