from app.database.db import db
from app.models.workspace import Workspace
from app.models.repository import Repository
from app.repositories.workspace_repository import WorkspaceRepository, _UNSET


class WorkspaceService:
    def __init__(self, repository=None):
        self.repository = repository or WorkspaceRepository()

    def create_workspace(self, name, slug, description=None, repository_ids=None):
        existing = self.repository.get_by_slug(slug)
        if existing:
            raise ValueError(f"Workspace with slug '{slug}' already exists.")

        workspace = Workspace(
            name=name,
            slug=slug,
            description=description,
        )

        if repository_ids:
            for repo_id in repository_ids:
                repo = db.session.get(Repository, repo_id)
                if repo:
                    workspace.repositories.append(repo)

        return self.repository.create(workspace)

    def get_all_workspaces(self):
        return self.repository.get_all()

    def get_workspace_by_slug(self, slug):
        return self.repository.get_by_slug(slug)

    def get_workspace_by_id(self, workspace_id):
        return self.repository.get_by_id(workspace_id)

    def update_workspace(self, current_slug, name=_UNSET, slug=_UNSET, description=_UNSET, repository_ids=_UNSET):
        workspace = self.repository.get_by_slug(current_slug)
        if not workspace:
            raise LookupError(f"Workspace with slug '{current_slug}' not found.")

        if slug is not _UNSET and slug != current_slug:
            existing = self.repository.get_by_slug(slug)
            if existing:
                raise ValueError(f"Workspace with slug '{slug}' already exists.")

        if repository_ids is not _UNSET and repository_ids is not None:
            # Sync repositories
            target_repos = []
            for repo_id in repository_ids:
                repo = db.session.get(Repository, repo_id)
                if repo:
                    target_repos.append(repo)
            workspace.repositories = target_repos

        return self.repository.update(
            workspace,
            name=name,
            slug=slug,
            description=description,
        )

    def delete_workspace(self, slug):
        workspace = self.repository.get_by_slug(slug)
        if not workspace:
            raise LookupError(f"Workspace with slug '{slug}' not found.")

        ws_id = workspace.id
        ws_name = workspace.name
        self.repository.delete(workspace)
        return {"id": ws_id, "slug": slug, "name": ws_name}

    def add_repository_to_workspace(self, workspace_slug, repository_slug):
        workspace = self.repository.get_by_slug(workspace_slug)
        if not workspace:
            raise LookupError(f"Workspace with slug '{workspace_slug}' not found.")

        repository = Repository.query.filter_by(slug=repository_slug).first()
        if not repository:
            raise LookupError(f"Repository with slug '{repository_slug}' not found.")

        return self.repository.add_repository(workspace, repository)

    def remove_repository_from_workspace(self, workspace_slug, repository_slug):
        workspace = self.repository.get_by_slug(workspace_slug)
        if not workspace:
            raise LookupError(f"Workspace with slug '{workspace_slug}' not found.")

        repository = Repository.query.filter_by(slug=repository_slug).first()
        if not repository:
            raise LookupError(f"Repository with slug '{repository_slug}' not found.")

        return self.repository.remove_repository(workspace, repository)
