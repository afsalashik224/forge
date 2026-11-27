import pytest
from app.models.repository import Repository
from app.models.workspace import Workspace
from app.models.concept import Concept


def test_create_repository_success(app, repo_service):
    repo = repo_service.create_repository(
        name="Ingress Controller",
        slug="ingress-controller",
        description="Edge ingress gateway",
        vcs_url="https://github.com/forge/ingress.git",
        primary_language="Go",
        status="ACTIVE",
    )
    assert repo.id is not None
    assert repo.name == "Ingress Controller"
    assert repo.slug == "ingress-controller"
    assert repo.primary_language == "Go"
    assert repo.status == "ACTIVE"


def test_create_repository_with_workspaces_and_concepts(app, repo_service, workspace_service, service):
    ws = workspace_service.create_workspace(name="Edge Network", slug="edge-network")
    c = service.create_concept(title="Edge Routing", slug="edge-routing", summary="Layer 7 reverse proxy routing")

    repo = repo_service.create_repository(
        name="Edge Router",
        slug="edge-router",
        workspace_ids=[ws.id],
        concept_ids=[c.id],
    )
    assert len(repo.workspaces) == 1
    assert repo.workspaces[0].slug == "edge-network"
    assert len(repo.concepts) == 1
    assert repo.concepts[0].slug == "edge-routing"


def test_create_repository_duplicate_slug_rejected(app, repo_service):
    repo_service.create_repository(name="Repo 1", slug="repo-dup")
    with pytest.raises(ValueError) as excinfo:
        repo_service.create_repository(name="Repo 2", slug="repo-dup")
    assert "already exists" in str(excinfo.value)


def test_get_repository_by_slug_existing_and_nonexistent(app, repo_service):
    repo_service.create_repository(name="API Gateway", slug="api-gateway")

    found = repo_service.get_repository_by_slug("api-gateway")
    assert found is not None
    assert found.name == "API Gateway"

    assert repo_service.get_repository_by_slug("non-existent") is None


def test_update_repository_success(app, repo_service):
    repo_service.create_repository(name="Old Repo", slug="old-repo", status="ACTIVE")

    updated = repo_service.update_repository(
        current_slug="old-repo",
        name="Updated Repo",
        slug="updated-repo",
        description="Updated desc",
        primary_language="TypeScript",
        status="MAINTENANCE",
    )
    assert updated.name == "Updated Repo"
    assert updated.slug == "updated-repo"
    assert updated.primary_language == "TypeScript"
    assert updated.status == "MAINTENANCE"


def test_update_repository_keep_same_slug(app, repo_service):
    repo_service.create_repository(name="Same Slug Repo", slug="same-slug-repo")

    updated = repo_service.update_repository(
        current_slug="same-slug-repo",
        name="New Title",
        slug="same-slug-repo",
    )
    assert updated.name == "New Title"
    assert updated.slug == "same-slug-repo"


def test_update_repository_duplicate_slug_rejected(app, repo_service):
    repo_service.create_repository(name="R1", slug="r1")
    repo_service.create_repository(name="R2", slug="r2")

    with pytest.raises(ValueError) as excinfo:
        repo_service.update_repository(current_slug="r2", slug="r1")
    assert "already exists" in str(excinfo.value)


def test_update_repository_nonexistent_raises_lookup_error(app, repo_service):
    with pytest.raises(LookupError) as excinfo:
        repo_service.update_repository(current_slug="missing-repo", name="Any Name")
    assert "not found" in str(excinfo.value)


def test_delete_repository_success_and_nonexistent(app, repo_service):
    repo_service.create_repository(name="Delete Me", slug="delete-me")
    res = repo_service.delete_repository("delete-me")
    assert res["slug"] == "delete-me"
    assert repo_service.get_repository_by_slug("delete-me") is None

    with pytest.raises(LookupError) as excinfo:
        repo_service.delete_repository("delete-me")
    assert "not found" in str(excinfo.value)


def test_add_and_remove_concept_from_repository(app, repo_service, service):
    repo = repo_service.create_repository(name="Message Broker", slug="message-broker")
    concept = service.create_concept(title="PubSub", slug="pub-sub", summary="Publish Subscribe pattern")

    # Add concept
    updated_repo = repo_service.add_concept_to_repository("message-broker", "pub-sub")
    assert len(updated_repo.concepts) == 1

    # Remove concept
    updated_repo = repo_service.remove_concept_from_repository("message-broker", "pub-sub")
    assert len(updated_repo.concepts) == 0

    # Nonexistent repo raises LookupError
    with pytest.raises(LookupError):
        repo_service.add_concept_to_repository("missing-repo", "pub-sub")

    # Nonexistent concept raises LookupError
    with pytest.raises(LookupError):
        repo_service.add_concept_to_repository("message-broker", "missing-concept")
