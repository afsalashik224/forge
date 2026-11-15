import time
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.exc import IntegrityError
from app.models.concept import Concept
from app.database.db import db


def test_repository_create_and_get_by_id(app, repository):
    concept = Concept(
        title="SQLAlchemy ORM",
        slug="sqlalchemy-orm",
        summary="Object relational mapper for Python."
    )
    saved = repository.create(concept)
    assert saved.id is not None
    assert saved.created_at is not None

    retrieved = repository.get_by_id(saved.id)
    assert retrieved is not None
    assert retrieved.id == saved.id
    assert retrieved.title == "SQLAlchemy ORM"


def test_repository_get_by_slug(app, repository):
    concept = Concept(
        title="Git Version Control",
        slug="git-vcs",
        summary="Distributed revision control."
    )
    repository.create(concept)

    found = repository.get_by_slug("git-vcs")
    assert found is not None
    assert found.slug == "git-vcs"

    not_found = repository.get_by_slug("unknown")
    assert not_found is None


def test_repository_get_all(app, repository):
    assert repository.get_all() == []

    c1 = Concept(title="T1", slug="s1", summary="Sum1")
    c2 = Concept(title="T2", slug="s2", summary="Sum2")
    repository.create(c1)
    repository.create(c2)

    all_concepts = repository.get_all()
    assert len(all_concepts) == 2


def test_concept_timestamp_semantics(app, repository):
    concept = Concept(
        title="Timestamp Test",
        slug="timestamp-test",
        summary="Testing created_at vs updated_at."
    )
    saved = repository.create(concept)
    initial_created = saved.created_at
    assert initial_created is not None

    # Simulate an update
    saved.summary = "Updated summary."
    db.session.commit()

    reloaded = repository.get_by_slug("timestamp-test")
    # created_at should NOT change
    assert reloaded.created_at == initial_created
    assert reloaded.summary == "Updated summary."


def test_repository_update_fields(app, repository):
    concept = Concept(title="Original", slug="original-slug", summary="Orig summary", status="DRAFT")
    repository.create(concept)

    updated = repository.update(
        concept,
        title="Updated Title",
        slug="new-slug",
        summary="New summary",
        status="PUBLISHED"
    )

    assert updated.title == "Updated Title"
    assert updated.slug == "new-slug"
    assert updated.summary == "New summary"
    assert updated.status == "PUBLISHED"

    # Verify retrieval by new slug
    found = repository.get_by_slug("new-slug")
    assert found is not None
    assert found.title == "Updated Title"


def test_repository_update_timestamp_advancement(app, repository):
    # Set a deterministic older timestamp
    older_time = datetime(2025, 1, 1, 12, 0, 0)
    concept = Concept(title="Timer", slug="timer", summary="Timer test", created_at=older_time, updated_at=older_time)
    repository.create(concept)

    assert concept.created_at == older_time
    assert concept.updated_at == older_time

    # Update via repository with explicit new timestamp commit
    time.sleep(0.01)
    repository.update(concept, title="Timer Updated")

    reloaded = repository.get_by_slug("timer")
    assert reloaded.created_at == older_time  # created_at preserved
    assert reloaded.updated_at >= older_time  # updated_at advanced or equal to current


def test_repository_update_duplicate_slug_raises_integrity_error(app, repository):
    c1 = Concept(title="First", slug="first", summary="Sum 1")
    c2 = Concept(title="Second", slug="second", summary="Sum 2")
    repository.create(c1)
    repository.create(c2)

    with pytest.raises(IntegrityError):
        repository.update(c2, slug="first")

    # Session rollback should keep c2 intact
    reloaded = repository.get_by_slug("second")
    assert reloaded is not None
    assert reloaded.title == "Second"


def test_repository_delete(app, repository):
    concept = Concept(title="To Delete", slug="to-delete", summary="Will be deleted")
    repository.create(concept)
    concept_id = concept.id

    assert repository.get_by_id(concept_id) is not None
    assert repository.delete(concept) is True
    assert repository.get_by_id(concept_id) is None
    assert repository.get_by_slug("to-delete") is None


def test_repository_update_omitted_summary_preserves_existing(app, repository):
    concept = Concept(title="Original", slug="preserve-test", summary="Initial Summary")
    repository.create(concept)

    # Update title only, summary is omitted
    updated = repository.update(concept, title="Changed Title")
    assert updated.title == "Changed Title"
    assert updated.summary == "Initial Summary"


def test_repository_update_none_summary_clears_existing(app, repository):
    concept = Concept(title="Original", slug="clear-none-test", summary="To be cleared")
    repository.create(concept)

    updated = repository.update(concept, summary=None)
    assert updated.summary is None


def test_repository_update_empty_string_summary_clears_existing(app, repository):
    concept = Concept(title="Original", slug="clear-empty-test", summary="To be cleared")
    repository.create(concept)

    updated = repository.update(concept, summary="")
    assert updated.summary == ""


def test_repository_not_null_integrity_error(app, repository):
    concept = Concept(title="Valid", slug="not-null-test", summary="Sum")
    repository.create(concept)

    # Setting title to None triggers NOT NULL integrity failure on concepts.title
    with pytest.raises(IntegrityError):
        repository.update(concept, title=None)

    # Rollback preserves valid concept
    reloaded = repository.get_by_slug("not-null-test")
    assert reloaded is not None
    assert reloaded.title == "Valid"
