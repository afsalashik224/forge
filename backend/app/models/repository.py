from app.database.db import db
from app.models.workspace import workspace_repositories

# Association table between Repositories and Concepts
repository_concepts = db.Table(
    "repository_concepts",
    db.Column("repository_id", db.Integer, db.ForeignKey("repositories.id", ondelete="CASCADE"), primary_key=True),
    db.Column("concept_id", db.Integer, db.ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
    db.Column("created_at", db.DateTime, server_default=db.func.now(), nullable=False),
)


class Repository(db.Model):
    __tablename__ = "repositories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(140), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    vcs_url = db.Column(db.String(300), nullable=True)
    primary_language = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")

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

    workspaces = db.relationship(
        "Workspace",
        secondary=workspace_repositories,
        back_populates="repositories",
        lazy="select",
    )

    concepts = db.relationship(
        "Concept",
        secondary=repository_concepts,
        back_populates="repositories",
        lazy="select",
    )

    def __repr__(self):
        return f"<Repository {self.name} ({self.slug})>"
