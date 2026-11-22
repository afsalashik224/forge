import pytest
from app.models.concept import Concept


def test_create_concept_success(app, service):
    concept = service.create_concept(
        title="Distributed Caching",
        slug="distributed-caching",
        summary="Cache eviction policies and partitioning."
    )
    assert concept.id is not None
    assert concept.title == "Distributed Caching"
    assert concept.slug == "distributed-caching"
    assert concept.summary == "Cache eviction policies and partitioning."
    assert concept.status == "DRAFT"
    assert concept.created_at is not None


def test_create_concept_duplicate_slug_rejected(app, service):
    service.create_concept(
        title="First Concept",
        slug="duplicate-slug",
        summary="First description."
    )
    with pytest.raises(ValueError) as excinfo:
        service.create_concept(
            title="Second Concept",
            slug="duplicate-slug",
            summary="Second description."
        )
    assert "already exists" in str(excinfo.value)


def test_get_concept_by_slug_existing(app, service):
    created = service.create_concept(
        title="REST APIs",
        slug="rest-apis",
        summary="Architectural style for networked apps."
    )
    found = service.get_concept_by_slug("rest-apis")
    assert found is not None
    assert found.id == created.id
    assert found.title == "REST APIs"


def test_get_concept_by_slug_nonexistent(app, service):
    found = service.get_concept_by_slug("nonexistent-slug")
    assert found is None


def test_get_all_concepts_empty_and_populated(app, service):
    assert service.get_all_concepts() == []

    service.create_concept(title="C1", slug="c1", summary="S1")
    service.create_concept(title="C2", slug="c2", summary="S2")

    concepts = service.get_all_concepts()
    assert len(concepts) == 2
    slugs = {c.slug for c in concepts}
    assert slugs == {"c1", "c2"}


def test_update_concept_success(app, service):
    service.create_concept(title="Old Title", slug="old-slug", summary="Old summary")
    
    updated = service.update_concept(
        current_slug="old-slug",
        title="New Title",
        slug="new-slug",
        summary="New summary",
        status="PUBLISHED"
    )
    assert updated.title == "New Title"
    assert updated.slug == "new-slug"
    assert updated.summary == "New summary"
    assert updated.status == "PUBLISHED"

    # Old slug should no longer exist
    assert service.get_concept_by_slug("old-slug") is None
    # New slug should exist
    assert service.get_concept_by_slug("new-slug") is not None


def test_update_concept_keep_same_slug(app, service):
    service.create_concept(title="Original", slug="same-slug", summary="Original summary")
    
    updated = service.update_concept(
        current_slug="same-slug",
        title="Modified Title",
        slug="same-slug",
        summary="Modified summary"
    )
    assert updated.title == "Modified Title"
    assert updated.slug == "same-slug"
    assert updated.summary == "Modified summary"
    # Status should be preserved when None
    assert updated.status == "DRAFT"


def test_update_concept_duplicate_slug_rejected(app, service):
    service.create_concept(title="First", slug="slug-one", summary="First concept")
    service.create_concept(title="Second", slug="slug-two", summary="Second concept")

    with pytest.raises(ValueError) as excinfo:
        service.update_concept(
            current_slug="slug-two",
            title="Second Updated",
            slug="slug-one"
        )
    assert "already exists" in str(excinfo.value)


def test_update_concept_nonexistent_raises_lookup_error(app, service):
    with pytest.raises(LookupError) as excinfo:
        service.update_concept(
            current_slug="missing-slug",
            title="Any Title",
            slug="any-slug"
        )
    assert "not found" in str(excinfo.value)


def test_delete_concept_success(app, service):
    service.create_concept(title="To Delete", slug="delete-me", summary="Summary")
    assert service.get_concept_by_slug("delete-me") is not None

    result = service.delete_concept("delete-me")
    assert result["slug"] == "delete-me"
    assert service.get_concept_by_slug("delete-me") is None


def test_delete_concept_nonexistent_raises_lookup_error(app, service):
    with pytest.raises(LookupError) as excinfo:
        service.delete_concept("no-such-concept")
    assert "not found" in str(excinfo.value)
