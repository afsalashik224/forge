import pytest
from sqlalchemy.exc import IntegrityError
from app.models.repository import Repository
from app.models.workspace import Workspace
from app.models.concept import Concept


def test_repository_repository_create_and_get_by_id(app, repo_repository):
    repo = Repository(
        name="Auth Service",
        slug="auth-service",
        description="OAuth2 and session handling service",
        vcs_url="https://github.com/forge/auth-service.git",
        primary_language="Python",
        status="ACTIVE",
    )
    created = repo_repository.create(repo)
    assert created.id is not None
    assert created.name == "Auth Service"
    assert created.slug == "auth-service"
    assert created.primary_language == "Python"
    assert created.status == "ACTIVE"

    fetched = repo_repository.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id


def test_repository_repository_get_by_slug(app, repo_repository):
    repo = Repository(name="Billing API", slug="billing-api")
    repo_repository.create(repo)

    found = repo_repository.get_by_slug("billing-api")
    assert found is not None
    assert found.slug == "billing-api"

    assert repo_repository.get_by_slug("unknown-slug") is None


def test_repository_repository_get_all(app, repo_repository):
    assert repo_repository.get_all() == []

    r1 = Repository(name="Zeta Repo", slug="zeta-repo")
    r2 = Repository(name="Alpha Repo", slug="alpha-repo")
    repo_repository.create(r1)
    repo_repository.create(r2)

    all_repos = repo_repository.get_all()
    assert len(all_repos) == 2
    assert all_repos[0].name == "Alpha Repo"
    assert all_repos[1].name == "Zeta Repo"


def test_repository_repository_update_fields(app, repo_repository):
    repo = Repository(name="Old Name", slug="old-slug", status="ACTIVE")
    repo_repository.create(repo)

    updated = repo_repository.update(
        repo,
        name="New Repo",
        slug="new-repo",
        description="Updated description",
        vcs_url="https://github.com/forge/new-repo.git",
        primary_language="Go",
        status="MAINTENANCE",
    )
    assert updated.name == "New Repo"
    assert updated.slug == "new-repo"
    assert updated.primary_language == "Go"
    assert updated.status == "MAINTENANCE"


def test_repository_repository_update_duplicate_slug_raises_integrity_error(app, repo_repository):
    r1 = Repository(name="Repo 1", slug="repo-1")
    r2 = Repository(name="Repo 2", slug="repo-2")
    repo_repository.create(r1)
    repo_repository.create(r2)

    with pytest.raises(IntegrityError):
        repo_repository.update(r2, slug="repo-1")


def test_repository_repository_delete(app, repo_repository):
    repo = Repository(name="To Delete", slug="to-delete")
    repo_repository.create(repo)

    assert repo_repository.delete(repo) is True
    assert repo_repository.get_by_slug("to-delete") is None


def test_repository_repository_add_and_remove_workspace(app, repo_repository, workspace_repository):
    repo = Repository(name="Worker Engine", slug="worker-engine")
    repo_repository.create(repo)

    ws = Workspace(name="Core WS", slug="core-ws")
    workspace_repository.create(ws)

    # Link workspace
    repo_repository.add_workspace(repo, ws)
    assert len(repo.workspaces) == 1
    assert repo.workspaces[0].slug == "core-ws"

    # Remove workspace
    repo_repository.remove_workspace(repo, ws)
    assert len(repo.workspaces) == 0


def test_repository_repository_add_and_remove_concept(app, repo_repository, repository):
    repo = Repository(name="Gateway Service", slug="gateway-service")
    repo_repository.create(repo)

    concept = Concept(title="Rate Limiting", slug="rate-limiting", summary="Token bucket rate limiter")
    repository.create(concept)

    # Link concept
    repo_repository.add_concept(repo, concept)
    assert len(repo.concepts) == 1
    assert repo.concepts[0].slug == "rate-limiting"
    assert len(concept.repositories) == 1
    assert concept.repositories[0].slug == "gateway-service"

    # Remove concept
    repo_repository.remove_concept(repo, concept)
    assert len(repo.concepts) == 0
    assert len(concept.repositories) == 0
