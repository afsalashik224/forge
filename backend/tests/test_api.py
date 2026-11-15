import json


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["application"] == "Forge"
    assert "version" in data
    assert "environment" in data


def test_get_concepts_empty_initially(client):
    response = client.get("/api/concepts/")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_concept_success_201(client):
    payload = {
        "title": "Clean Architecture",
        "slug": "clean-architecture",
        "summary": "Separation of concerns by layers."
    }
    response = client.post(
        "/api/concepts/",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 201
    res = response.get_json()
    assert res["message"] == "Concept created successfully."
    assert res["data"]["title"] == "Clean Architecture"
    assert res["data"]["slug"] == "clean-architecture"
    assert res["data"]["status"] == "DRAFT"
    assert res["data"]["created_at"] is not None


def test_create_concept_non_json_returns_400(client):
    response = client.post(
        "/api/concepts/",
        data="raw string",
        content_type="text/plain"
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_concept_missing_title_returns_400(client):
    payload = {"slug": "no-title", "summary": "Some summary"}
    response = client.post(
        "/api/concepts/",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_concept_empty_title_returns_400(client):
    payload = {"title": "   ", "slug": "empty-title", "summary": "Some summary"}
    response = client.post(
        "/api/concepts/",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_concept_missing_slug_returns_400(client):
    payload = {"title": "No Slug", "summary": "Some summary"}
    response = client.post(
        "/api/concepts/",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_concept_invalid_type_returns_400(client):
    payload = {"title": 12345, "slug": "numeric-title", "summary": "Some summary"}
    response = client.post(
        "/api/concepts/",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_concept_duplicate_slug_returns_409(client):
    payload = {
        "title": "Idempotence",
        "slug": "idempotence",
        "summary": "An operation that can be applied multiple times without changing the result."
    }
    # First creation -> 201
    r1 = client.post(
        "/api/concepts/",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert r1.status_code == 201

    # Second creation with same slug -> 409
    r2 = client.post(
        "/api/concepts/",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert r2.status_code == 409
    assert "error" in r2.get_json()
    assert "already exists" in r2.get_json()["error"]


def test_get_concept_by_slug_found_and_not_found(client):
    # Not found
    r_404 = client.get("/api/concepts/missing-concept")
    assert r_404.status_code == 404
    assert "error" in r_404.get_json()

    # Create then get
    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Docker", "slug": "docker", "summary": "Containerization platform."}),
        content_type="application/json"
    )
    r_200 = client.get("/api/concepts/docker")
    assert r_200.status_code == 200
    data = r_200.get_json()
    assert data["title"] == "Docker"
    assert data["slug"] == "docker"
    assert data["created_at"] is not None


def test_get_all_concepts_returns_list(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "A", "slug": "a", "summary": "sum a"}),
        content_type="application/json"
    )
    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "B", "slug": "b", "summary": "sum b"}),
        content_type="application/json"
    )
    response = client.get("/api/concepts/")
    assert response.status_code == 200
    concepts = response.get_json()
    assert len(concepts) == 2
    assert concepts[0]["slug"] == "a"
    assert concepts[1]["slug"] == "b"


def test_update_concept_200_ok(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Initial", "slug": "initial-slug", "summary": "Initial summary"}),
        content_type="application/json"
    )

    update_payload = {
        "title": "Updated Title",
        "slug": "updated-slug",
        "summary": "Updated summary",
        "status": "PUBLISHED"
    }
    response = client.put(
        "/api/concepts/initial-slug",
        data=json.dumps(update_payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    res = response.get_json()
    assert res["message"] == "Concept updated successfully."
    assert res["data"]["title"] == "Updated Title"
    assert res["data"]["slug"] == "updated-slug"
    assert res["data"]["summary"] == "Updated summary"
    assert res["data"]["status"] == "PUBLISHED"
    assert res["data"]["updated_at"] is not None

    # Verify old slug 404s and new slug 200s
    assert client.get("/api/concepts/initial-slug").status_code == 404
    assert client.get("/api/concepts/updated-slug").status_code == 200


def test_update_concept_preserve_status_when_omitted(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Status Test", "slug": "status-test", "summary": "Status test summary"}),
        content_type="application/json"
    )

    # PUT without status field
    update_payload = {
        "title": "Status Test Updated",
        "slug": "status-test",
        "summary": "Updated without status"
    }
    response = client.put(
        "/api/concepts/status-test",
        data=json.dumps(update_payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    # Status should remain DRAFT (not reset to None or anything else)
    assert response.get_json()["data"]["status"] == "DRAFT"


def test_update_concept_non_json_returns_400(client):
    response = client.put(
        "/api/concepts/any-slug",
        data="raw text",
        content_type="text/plain"
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_update_concept_missing_title_or_slug_returns_400(client):
    # Missing title
    r1 = client.put(
        "/api/concepts/some-slug",
        data=json.dumps({"slug": "new-slug"}),
        content_type="application/json"
    )
    assert r1.status_code == 400

    # Missing slug
    r2 = client.put(
        "/api/concepts/some-slug",
        data=json.dumps({"title": "New Title"}),
        content_type="application/json"
    )
    assert r2.status_code == 400


def test_update_concept_empty_title_or_slug_returns_400(client):
    r1 = client.put(
        "/api/concepts/some-slug",
        data=json.dumps({"title": "   ", "slug": "valid-slug"}),
        content_type="application/json"
    )
    assert r1.status_code == 400

    r2 = client.put(
        "/api/concepts/some-slug",
        data=json.dumps({"title": "Valid Title", "slug": "   "}),
        content_type="application/json"
    )
    assert r2.status_code == 400


def test_update_concept_invalid_status_returns_400(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Valid", "slug": "valid-concept", "summary": "Sum"}),
        content_type="application/json"
    )
    response = client.put(
        "/api/concepts/valid-concept",
        data=json.dumps({"title": "Valid", "slug": "valid-concept", "status": "INVALID_STATUS"}),
        content_type="application/json"
    )
    assert response.status_code == 400
    assert "status" in response.get_json()["error"]


def test_update_concept_not_found_returns_404(client):
    response = client.put(
        "/api/concepts/nonexistent-slug",
        data=json.dumps({"title": "Title", "slug": "slug"}),
        content_type="application/json"
    )
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_update_concept_duplicate_slug_returns_409(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Alpha", "slug": "alpha", "summary": "A"}),
        content_type="application/json"
    )
    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Beta", "slug": "beta", "summary": "B"}),
        content_type="application/json"
    )

    # Try updating Beta to have slug "alpha"
    response = client.put(
        "/api/concepts/beta",
        data=json.dumps({"title": "Beta", "slug": "alpha"}),
        content_type="application/json"
    )
    assert response.status_code == 409
    assert "already exists" in response.get_json()["error"]


def test_delete_concept_200_ok(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Doomed", "slug": "doomed", "summary": "To be removed"}),
        content_type="application/json"
    )
    assert client.get("/api/concepts/doomed").status_code == 200

    response = client.delete("/api/concepts/doomed")
    assert response.status_code == 200
    res = response.get_json()
    assert res["message"] == "Concept deleted successfully."
    assert res["data"]["slug"] == "doomed"

    # Confirmed deleted
    assert client.get("/api/concepts/doomed").status_code == 404


def test_delete_concept_not_found_returns_404(client):
    response = client.delete("/api/concepts/missing-concept")
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_crud_lifecycle_regression(client):
    # 1. CREATE
    c_res = client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Full Cycle", "slug": "full-cycle", "summary": "Testing CRUD"}),
        content_type="application/json"
    )
    assert c_res.status_code == 201
    
    # 2. READ
    r_res = client.get("/api/concepts/full-cycle")
    assert r_res.status_code == 200
    assert r_res.get_json()["title"] == "Full Cycle"

    # 3. UPDATE
    u_res = client.put(
        "/api/concepts/full-cycle",
        data=json.dumps({"title": "Full Cycle Updated", "slug": "full-cycle-v2", "summary": "Updated CRUD"}),
        content_type="application/json"
    )
    assert u_res.status_code == 200
    assert u_res.get_json()["data"]["slug"] == "full-cycle-v2"
    assert client.get("/api/concepts/full-cycle").status_code == 404
    assert client.get("/api/concepts/full-cycle-v2").status_code == 200

    # 4. DELETE
    d_res = client.delete("/api/concepts/full-cycle-v2")
    assert d_res.status_code == 200


def test_update_concept_omitted_summary_preserves_existing(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Keep Summary", "slug": "keep-summary", "summary": "Initial summary"}),
        content_type="application/json"
    )
    # PUT with summary omitted
    response = client.put(
        "/api/concepts/keep-summary",
        data=json.dumps({"title": "Updated Title", "slug": "keep-summary"}),
        content_type="application/json"
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["summary"] == "Initial summary"


def test_update_concept_null_summary_clears_existing(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Clear Null", "slug": "clear-null", "summary": "Initial summary"}),
        content_type="application/json"
    )
    # PUT with summary = null
    response = client.put(
        "/api/concepts/clear-null",
        data=json.dumps({"title": "Clear Null", "slug": "clear-null", "summary": None}),
        content_type="application/json"
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["summary"] is None


def test_update_concept_empty_string_summary_clears_existing(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Clear Empty", "slug": "clear-empty", "summary": "Initial summary"}),
        content_type="application/json"
    )
    # PUT with summary = ""
    response = client.put(
        "/api/concepts/clear-empty",
        data=json.dumps({"title": "Clear Empty", "slug": "clear-empty", "summary": ""}),
        content_type="application/json"
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["summary"] is None


def test_update_concept_non_string_non_null_summary_returns_400(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Summary Type", "slug": "summary-type", "summary": "Initial"}),
        content_type="application/json"
    )
    response = client.put(
        "/api/concepts/summary-type",
        data=json.dumps({"title": "Summary Type", "slug": "summary-type", "summary": 12345}),
        content_type="application/json"
    )
    assert response.status_code == 400
    assert "summary" in response.get_json()["error"]


def test_update_concept_integrity_error_other_than_duplicate_slug_returns_400(client, monkeypatch):
    from sqlalchemy.exc import IntegrityError
    from app.api import concept_api

    client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Integrity Test", "slug": "integrity-test", "summary": "Initial"}),
        content_type="application/json"
    )

    def mock_update(*args, **kwargs):
        raise IntegrityError("statement", "params", Exception("CHECK constraint failed: concepts"))

    monkeypatch.setattr(concept_api.service, "update_concept", mock_update)

    response = client.put(
        "/api/concepts/integrity-test",
        data=json.dumps({"title": "New Title", "slug": "integrity-test"}),
        content_type="application/json"
    )
    assert response.status_code == 400
    assert "integrity" in response.get_json()["error"].lower()
    assert "already exists" not in response.get_json()["error"].lower()


def test_unexpected_exception_logged(client, monkeypatch, caplog):
    from app.api import concept_api
    import logging

    def mock_fail(*args, **kwargs):
        raise RuntimeError("Database connection suddenly dropped")

    monkeypatch.setattr(concept_api.service, "get_all_concepts", mock_fail)

    with caplog.at_level(logging.ERROR):
        response = client.get("/api/concepts/")
        assert response.status_code == 500
        assert response.get_json()["error"] == "An unexpected error occurred while fetching concepts."
        assert any("Database connection suddenly dropped" in record.message or "Unexpected error" in record.message for record in caplog.records)
    assert client.get("/api/concepts/full-cycle-v2").status_code == 404
