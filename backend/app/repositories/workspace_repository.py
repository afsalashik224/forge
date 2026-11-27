from sqlalchemy.exc import IntegrityError
from app.database.db import db
from app.models.workspace import Workspace

_UNSET = object()


class WorkspaceRepository:
    def create(self, workspace):
        try:
            db.session.add(workspace)
            db.session.commit()
            return workspace
        except IntegrityError:
            db.session.rollback()
            raise

    def get_by_id(self, workspace_id):
        return db.session.get(Workspace, workspace_id)

    def get_by_slug(self, slug):
        return Workspace.query.filter_by(slug=slug).first()

    def get_all(self):
        return Workspace.query.order_by(Workspace.name.asc()).all()

    def update(self, workspace, name=_UNSET, slug=_UNSET, description=_UNSET):
        try:
            if name is not _UNSET:
                workspace.name = name
            if slug is not _UNSET:
                workspace.slug = slug
            if description is not _UNSET:
                workspace.description = description
            db.session.commit()
            return workspace
        except IntegrityError:
            db.session.rollback()
            raise

    def delete(self, workspace):
        try:
            db.session.delete(workspace)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise

    def add_repository(self, workspace, repository):
        try:
            if repository not in workspace.repositories:
                workspace.repositories.append(repository)
                db.session.commit()
            return workspace
        except Exception:
            db.session.rollback()
            raise

    def remove_repository(self, workspace, repository):
        try:
            if repository in workspace.repositories:
                workspace.repositories.remove(repository)
                db.session.commit()
            return workspace
        except Exception:
            db.session.rollback()
            raise
