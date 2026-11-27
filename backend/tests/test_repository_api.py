import json


def test_get_repositories_empty_initially(client):
    response = client.get("/api/repositories/")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_repository_success_201(client):
    payload = {
        "name": "Frontend Web App",
        "slug": "frontend-web-app",
        "description": "React Vite SPA",
        "vcs_url": "https://github.com/forge/frontend.git",
        "primary_language": "TypeScript",
        "status": "ACTIVE",
    }
    response = client.post(
        "/api/repositories/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Repository created successfully."
    assert data["data"]["name"] == "Frontend Web App"
    assert data["data"]["slug"] == "frontend-web-app"
    assert data["data"]["primary_language"] == "TypeScript"
    assert data["data"]["status"] == "ACTIVE"


def test_create_repository_validation_errors(client):
    # Non-json
    res = client.post("/api/repositories/", data="not json", content_type="text/plain")
    assert res.status_code == 400

    # Missing name
    res = client.post(
        "/api/repositories/",
        data=json.dumps({"slug": "missing-name"}),
        content_type="application/json",
    )
    assert res.status_code == 400
    assert "Fields 'name' and 'slug' are required." in res.get_json()["error"]

    # Empty name
    res = client.post(
        "/api/repositories/",
        data=json.dumps({"name": "   ", "slug": "valid-slug"}),
        content_type="application/json",
    )
    assert res.status_code == 400
    assert "cannot be empty" in res.get_json()["error"]

    # Invalid status
    res = client.post(
        "/api/repositories/",
        data=json.dumps({"name": "Valid Name", "slug": "valid-slug", "status": "INVALID_STATUS"}),
        content_type="application/json",
    )
    assert res.status_code == 400
    assert "must be 'ACTIVE', 'ARCHIVED', or 'MAINTENANCE'" in res.get_json()["error"]


def test_create_repository_duplicate_slug_returns_409(client):
    payload = {"name": "Repo 1", "slug": "dup-repo"}
    res1 = client.post("/api/repositories/", data=json.dumps(payload), content_type="application/json")
    assert res1.status_code == 201

    res2 = client.post("/api/repositories/", data=json.dumps({"name": "Repo 2", "slug": "dup-repo"}), content_type="application/json")
    assert res2.status_code == 409
    assert "already exists" in res2.get_json()["error"]


def test_get_repository_by_slug_found_and_not_found(client):
    client.post("/api/repositories/", data=json.dumps({"name": "Auth Service", "slug": "auth-service"}), content_type="application/json")

    res = client.get("/api/repositories/auth-service")
    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "Auth Service"
    assert "workspaces" in data
    assert "concepts" in data

    res_404 = client.get("/api/repositories/missing-repo")
    assert res_404.status_code == 404


def test_update_repository_success_and_errors(client):
    client.post("/api/repositories/", data=json.dumps({"name": "Old Repo", "slug": "old-repo"}), content_type="application/json")

    # Update repo
    res = client.put(
        "/api/repositories/old-repo",
        data=json.dumps({"name": "New Repo", "slug": "new-repo", "status": "MAINTENANCE", "primary_language": "Python"}),
        content_type="application/json",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["data"]["name"] == "New Repo"
    assert data["data"]["slug"] == "new-repo"
    assert data["data"]["status"] == "MAINTENANCE"
    assert data["data"]["primary_language"] == "Python"

    # Non-json
    res = client.put("/api/repositories/new-repo", data="text", content_type="text/plain")
    assert res.status_code == 400

    # 404 update
    res = client.put("/api/repositories/missing-repo", data=json.dumps({"name": "New"}), content_type="application/json")
    assert res.status_code == 404


def test_delete_repository(client):
    client.post("/api/repositories/", data=json.dumps({"name": "Delete Repo", "slug": "delete-repo"}), content_type="application/json")

    res = client.delete("/api/repositories/delete-repo")
    assert res.status_code == 200
    assert "deleted successfully" in res.get_json()["message"]

    res_404 = client.delete("/api/repositories/delete-repo")
    assert res_404.status_code == 404


def test_link_and_unlink_concept_endpoint(client):
    # Create concept and repository
    client.post("/api/concepts/", data=json.dumps({"title": "OAuth 2.0", "slug": "oauth-2", "summary": "OAuth protocol"}), content_type="application/json")
    client.post("/api/repositories/", data=json.dumps({"name": "Auth Gateway", "slug": "auth-gateway"}), content_type="application/json")

    # Link concept
    res = client.post(
        "/api/repositories/auth-gateway/concepts",
        data=json.dumps({"concept_slug": "oauth-2"}),
        content_type="application/json",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["data"]["concepts"]) == 1
    assert data["data"]["concepts"][0]["slug"] == "oauth-2"

    # Unlink concept
    res = client.delete("/api/repositories/auth-gateway/concepts/oauth-2")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["data"]["concepts"]) == 0
