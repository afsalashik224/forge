from app.database.db import db

# Association table between Workspaces and Repositories
workspace_repositories = db.Table(
    "workspace_repositories",
    db.Column("workspace_id", db.Integer, db.ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True),
    db.Column("repository_id", db.Integer, db.ForeignKey("repositories.id", ondelete="CASCADE"), primary_key=True),
    db.Column("created_at", db.DateTime, server_default=db.func.now(), nullable=False),
)


class Workspace(db.Model):
    __tablename__ = "workspaces"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
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

    repositories = db.relationship(
        "Repository",
        secondary=workspace_repositories,
        back_populates="workspaces",
        lazy="select",
    )

    def __repr__(self):
        return f"<Workspace {self.name} ({self.slug})>"
