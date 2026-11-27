from sqlalchemy.exc import IntegrityError
from app.database.db import db
from app.models.repository import Repository

_UNSET = object()


class RepositoryRepository:
    def create(self, repository):
        try:
            db.session.add(repository)
            db.session.commit()
            return repository
        except IntegrityError:
            db.session.rollback()
            raise

    def get_by_id(self, repo_id):
        return db.session.get(Repository, repo_id)

    def get_by_slug(self, slug):
        return Repository.query.filter_by(slug=slug).first()

    def get_all(self):
        return Repository.query.order_by(Repository.name.asc()).all()

    def update(
        self,
        repository,
        name=_UNSET,
        slug=_UNSET,
        description=_UNSET,
        vcs_url=_UNSET,
        primary_language=_UNSET,
        status=_UNSET,
    ):
        try:
            if name is not _UNSET:
                repository.name = name
            if slug is not _UNSET:
                repository.slug = slug
            if description is not _UNSET:
                repository.description = description
            if vcs_url is not _UNSET:
                repository.vcs_url = vcs_url
            if primary_language is not _UNSET:
                repository.primary_language = primary_language
            if status is not _UNSET:
                repository.status = status
            db.session.commit()
            return repository
        except IntegrityError:
            db.session.rollback()
            raise

    def delete(self, repository):
        try:
            db.session.delete(repository)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            raise

    def add_workspace(self, repository, workspace):
        try:
            if workspace not in repository.workspaces:
                repository.workspaces.append(workspace)
                db.session.commit()
            return repository
        except Exception:
            db.session.rollback()
            raise

    def remove_workspace(self, repository, workspace):
        try:
            if workspace in repository.workspaces:
                repository.workspaces.remove(workspace)
                db.session.commit()
            return repository
        except Exception:
            db.session.rollback()
            raise

    def add_concept(self, repository, concept):
        try:
            if concept not in repository.concepts:
                repository.concepts.append(concept)
                db.session.commit()
            return repository
        except Exception:
            db.session.rollback()
            raise

    def remove_concept(self, repository, concept):
        try:
            if concept in repository.concepts:
                repository.concepts.remove(concept)
                db.session.commit()
            return repository
        except Exception:
            db.session.rollback()
            raise
