import pytest
from sqlalchemy.exc import IntegrityError
from app.models.workspace import Workspace
from app.models.repository import Repository


def test_workspace_repository_create_and_get_by_id(app, workspace_repository):
    ws = Workspace(name="Platform Core", slug="platform-core", description="Core platform workspace")
    created = workspace_repository.create(ws)
    assert created.id is not None
    assert created.name == "Platform Core"
    assert created.slug == "platform-core"

    fetched = workspace_repository.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Platform Core"


def test_workspace_repository_get_by_slug(app, workspace_repository):
    ws = Workspace(name="Infra Team", slug="infra-team", description="Infrastructure projects")
    workspace_repository.create(ws)

    found = workspace_repository.get_by_slug("infra-team")
    assert found is not None
    assert found.slug == "infra-team"

    assert workspace_repository.get_by_slug("non-existent") is None


def test_workspace_repository_get_all(app, workspace_repository):
    assert workspace_repository.get_all() == []

    ws1 = Workspace(name="Beta Workspace", slug="beta-ws")
    ws2 = Workspace(name="Alpha Workspace", slug="alpha-ws")
    workspace_repository.create(ws1)
    workspace_repository.create(ws2)

    all_ws = workspace_repository.get_all()
    assert len(all_ws) == 2
    # Ascending alphabetical order by name
    assert all_ws[0].name == "Alpha Workspace"
    assert all_ws[1].name == "Beta Workspace"


def test_workspace_repository_update_fields(app, workspace_repository):
    ws = Workspace(name="Original Name", slug="original-slug", description="Initial description")
    workspace_repository.create(ws)

    updated = workspace_repository.update(ws, name="New Name", slug="new-slug", description="Updated description")
    assert updated.name == "New Name"
    assert updated.slug == "new-slug"
    assert updated.description == "Updated description"


def test_workspace_repository_update_duplicate_slug_raises_integrity_error(app, workspace_repository):
    ws1 = Workspace(name="Workspace One", slug="ws-one")
    ws2 = Workspace(name="Workspace Two", slug="ws-two")
    workspace_repository.create(ws1)
    workspace_repository.create(ws2)

    with pytest.raises(IntegrityError):
        workspace_repository.update(ws2, slug="ws-one")


def test_workspace_repository_delete(app, workspace_repository):
    ws = Workspace(name="Temporary WS", slug="temp-ws")
    workspace_repository.create(ws)

    assert workspace_repository.delete(ws) is True
    assert workspace_repository.get_by_slug("temp-ws") is None


def test_workspace_repository_add_and_remove_repository(app, workspace_repository, repo_repository):
    ws = Workspace(name="Workspace With Repos", slug="ws-repos")
    workspace_repository.create(ws)

    repo = Repository(name="Microservice A", slug="microservice-a")
    repo_repository.create(repo)

    # Link repo
    workspace_repository.add_repository(ws, repo)
    assert len(ws.repositories) == 1
    assert ws.repositories[0].slug == "microservice-a"

    # Linking again is idempotent
    workspace_repository.add_repository(ws, repo)
    assert len(ws.repositories) == 1

    # Remove repo
    workspace_repository.remove_repository(ws, repo)
    assert len(ws.repositories) == 0
