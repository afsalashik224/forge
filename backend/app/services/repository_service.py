from app.database.db import db
from app.models.repository import Repository
from app.models.workspace import Workspace
from app.models.concept import Concept
from app.repositories.repository_repository import RepositoryRepository, _UNSET


class RepositoryService:
    def __init__(self, repository=None):
        self.repository = repository or RepositoryRepository()

    def create_repository(
        self,
        name,
        slug,
        description=None,
        vcs_url=None,
        primary_language=None,
        status="ACTIVE",
        workspace_ids=None,
        concept_ids=None,
    ):
        existing = self.repository.get_by_slug(slug)
        if existing:
            raise ValueError(f"Repository with slug '{slug}' already exists.")

        repo = Repository(
            name=name,
            slug=slug,
            description=description,
            vcs_url=vcs_url,
            primary_language=primary_language,
            status=status or "ACTIVE",
        )

        if workspace_ids:
            for ws_id in workspace_ids:
                ws = db.session.get(Workspace, ws_id)
                if ws:
                    repo.workspaces.append(ws)

        if concept_ids:
            for c_id in concept_ids:
                c = db.session.get(Concept, c_id)
                if c:
                    repo.concepts.append(c)

        return self.repository.create(repo)

    def get_all_repositories(self):
        return self.repository.get_all()

    def get_repository_by_slug(self, slug):
        return self.repository.get_by_slug(slug)

    def get_repository_by_id(self, repo_id):
        return self.repository.get_by_id(repo_id)

    def update_repository(
        self,
        current_slug,
        name=_UNSET,
        slug=_UNSET,
        description=_UNSET,
        vcs_url=_UNSET,
        primary_language=_UNSET,
        status=_UNSET,
        workspace_ids=_UNSET,
        concept_ids=_UNSET,
    ):
        repo = self.repository.get_by_slug(current_slug)
        if not repo:
            raise LookupError(f"Repository with slug '{current_slug}' not found.")

        if slug is not _UNSET and slug != current_slug:
            existing = self.repository.get_by_slug(slug)
            if existing:
                raise ValueError(f"Repository with slug '{slug}' already exists.")

        if workspace_ids is not _UNSET and workspace_ids is not None:
            target_workspaces = []
            for ws_id in workspace_ids:
                ws = db.session.get(Workspace, ws_id)
                if ws:
                    target_workspaces.append(ws)
            repo.workspaces = target_workspaces

        if concept_ids is not _UNSET and concept_ids is not None:
            target_concepts = []
            for c_id in concept_ids:
                c = db.session.get(Concept, c_id)
                if c:
                    target_concepts.append(c)
            repo.concepts = target_concepts

        return self.repository.update(
            repo,
            name=name,
            slug=slug,
            description=description,
            vcs_url=vcs_url,
            primary_language=primary_language,
            status=status,
        )

    def delete_repository(self, slug):
        repo = self.repository.get_by_slug(slug)
        if not repo:
            raise LookupError(f"Repository with slug '{slug}' not found.")

        repo_id = repo.id
        repo_name = repo.name
        self.repository.delete(repo)
        return {"id": repo_id, "slug": slug, "name": repo_name}

    def add_concept_to_repository(self, repository_slug, concept_slug):
        repo = self.repository.get_by_slug(repository_slug)
        if not repo:
            raise LookupError(f"Repository with slug '{repository_slug}' not found.")

        concept = Concept.query.filter_by(slug=concept_slug).first()
        if not concept:
            raise LookupError(f"Concept with slug '{concept_slug}' not found.")

        return self.repository.add_concept(repo, concept)

    def remove_concept_from_repository(self, repository_slug, concept_slug):
        repo = self.repository.get_by_slug(repository_slug)
        if not repo:
            raise LookupError(f"Repository with slug '{repository_slug}' not found.")

        concept = Concept.query.filter_by(slug=concept_slug).first()
        if not concept:
            raise LookupError(f"Concept with slug '{concept_slug}' not found.")

        return self.repository.remove_concept(repo, concept)

    def add_workspace_to_repository(self, repository_slug, workspace_slug):
        repo = self.repository.get_by_slug(repository_slug)
        if not repo:
            raise LookupError(f"Repository with slug '{repository_slug}' not found.")

        ws = Workspace.query.filter_by(slug=workspace_slug).first()
        if not ws:
            raise LookupError(f"Workspace with slug '{workspace_slug}' not found.")

        return self.repository.add_workspace(repo, ws)

    def remove_workspace_from_repository(self, repository_slug, workspace_slug):
        repo = self.repository.get_by_slug(repository_slug)
        if not repo:
            raise LookupError(f"Repository with slug '{repository_slug}' not found.")

        ws = Workspace.query.filter_by(slug=workspace_slug).first()
        if not ws:
            raise LookupError(f"Workspace with slug '{workspace_slug}' not found.")

        return self.repository.remove_workspace(repo, ws)
