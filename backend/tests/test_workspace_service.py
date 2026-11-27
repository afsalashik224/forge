import pytest
from app.models.workspace import Workspace
from app.models.repository import Repository


def test_create_workspace_success(app, workspace_service):
    ws = workspace_service.create_workspace(
        name="Backend Core",
        slug="backend-core",
        description="Core backend services and components.",
    )
    assert ws.id is not None
    assert ws.name == "Backend Core"
    assert ws.slug == "backend-core"
    assert ws.description == "Core backend services and components."


def test_create_workspace_with_repositories(app, workspace_service, repo_service):
    r1 = repo_service.create_repository(name="Service A", slug="service-a")
    r2 = repo_service.create_repository(name="Service B", slug="service-b")

    ws = workspace_service.create_workspace(
        name="Combined Workspace",
        slug="combined-ws",
        repository_ids=[r1.id, r2.id],
    )
    assert len(ws.repositories) == 2
    repo_slugs = {r.slug for r in ws.repositories}
    assert repo_slugs == {"service-a", "service-b"}


def test_create_workspace_duplicate_slug_rejected(app, workspace_service):
    workspace_service.create_workspace(name="WS 1", slug="duplicate-slug")
    with pytest.raises(ValueError) as excinfo:
        workspace_service.create_workspace(name="WS 2", slug="duplicate-slug")
    assert "already exists" in str(excinfo.value)


def test_get_workspace_by_slug_existing_and_nonexistent(app, workspace_service):
    workspace_service.create_workspace(name="Existing WS", slug="existing-ws")

    found = workspace_service.get_workspace_by_slug("existing-ws")
    assert found is not None
    assert found.name == "Existing WS"

    assert workspace_service.get_workspace_by_slug("nonexistent") is None


def test_update_workspace_success(app, workspace_service):
    workspace_service.create_workspace(name="Old WS", slug="old-ws", description="Old desc")

    updated = workspace_service.update_workspace(
        current_slug="old-ws",
        name="Updated WS",
        slug="updated-ws",
        description="New desc",
    )
    assert updated.name == "Updated WS"
    assert updated.slug == "updated-ws"
    assert updated.description == "New desc"


def test_update_workspace_keep_same_slug(app, workspace_service):
    workspace_service.create_workspace(name="Same Slug WS", slug="same-slug-ws")

    updated = workspace_service.update_workspace(
        current_slug="same-slug-ws",
        name="Changed Name",
        slug="same-slug-ws",
    )
    assert updated.name == "Changed Name"
    assert updated.slug == "same-slug-ws"


def test_update_workspace_duplicate_slug_rejected(app, workspace_service):
    workspace_service.create_workspace(name="WS One", slug="ws-one")
    workspace_service.create_workspace(name="WS Two", slug="ws-two")

    with pytest.raises(ValueError) as excinfo:
        workspace_service.update_workspace(current_slug="ws-two", slug="ws-one")
    assert "already exists" in str(excinfo.value)


def test_update_workspace_nonexistent_raises_lookup_error(app, workspace_service):
    with pytest.raises(LookupError) as excinfo:
        workspace_service.update_workspace(current_slug="missing-ws", name="Any Name")
    assert "not found" in str(excinfo.value)


def test_delete_workspace_success_and_nonexistent(app, workspace_service):
    workspace_service.create_workspace(name="To Delete", slug="to-delete")
    res = workspace_service.delete_workspace("to-delete")
    assert res["slug"] == "to-delete"
    assert workspace_service.get_workspace_by_slug("to-delete") is None

    with pytest.raises(LookupError) as excinfo:
        workspace_service.delete_workspace("to-delete")
    assert "not found" in str(excinfo.value)


def test_add_and_remove_repository_from_workspace(app, workspace_service, repo_service):
    ws = workspace_service.create_workspace(name="Target WS", slug="target-ws")
    repo = repo_service.create_repository(name="Target Repo", slug="target-repo")

    # Add repo
    updated_ws = workspace_service.add_repository_to_workspace("target-ws", "target-repo")
    assert len(updated_ws.repositories) == 1

    # Remove repo
    updated_ws = workspace_service.remove_repository_from_workspace("target-ws", "target-repo")
    assert len(updated_ws.repositories) == 0

    # Nonexistent WS raises LookupError
    with pytest.raises(LookupError):
        workspace_service.add_repository_to_workspace("missing-ws", "target-repo")

    # Nonexistent repo raises LookupError
    with pytest.raises(LookupError):
        workspace_service.add_repository_to_workspace("target-ws", "missing-repo")
