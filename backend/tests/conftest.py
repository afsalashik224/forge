import os
import sys
import pytest

# Ensure backend root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database.db import db
from app.repositories.concept_repository import ConceptRepository
from app.services.concept_service import ConceptService
from app.repositories.workspace_repository import WorkspaceRepository
from app.services.workspace_service import WorkspaceService
from app.repositories.repository_repository import RepositoryRepository
from app.services.repository_service import RepositoryService


@pytest.fixture
def app():
    """Create and configure a clean application instance for testing."""
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "test-secret-key",
    }
    app = create_app(test_config=test_config)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def repository(app):
    """A ConceptRepository bound to the test app context."""
    return ConceptRepository()


@pytest.fixture
def service(repository):
    """A ConceptService bound to the test repository."""
    return ConceptService(repository=repository)


@pytest.fixture
def workspace_repository(app):
    """A WorkspaceRepository bound to the test app context."""
    return WorkspaceRepository()


@pytest.fixture
def workspace_service(workspace_repository):
    """A WorkspaceService bound to the test workspace repository."""
    return WorkspaceService(repository=workspace_repository)


@pytest.fixture
def repo_repository(app):
    """A RepositoryRepository bound to the test app context."""
    return RepositoryRepository()


@pytest.fixture
def repo_service(repo_repository):
    """A RepositoryService bound to the test repository repository."""
    return RepositoryService(repository=repo_repository)
