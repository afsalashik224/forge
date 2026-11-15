import os
import sys
import pytest

# Ensure backend root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database.db import db
from app.repositories.concept_repository import ConceptRepository
from app.services.concept_service import ConceptService


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
