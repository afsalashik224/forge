import json


def test_get_workspaces_empty_initially(client):
    response = client.get("/api/workspaces/")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_workspace_success_201(client):
    payload = {
        "name": "Cloud Infrastructure",
        "slug": "cloud-infrastructure",
        "description": "AWS and Terraform configs",
    }
    response = client.post(
        "/api/workspaces/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Workspace created successfully."
    assert data["data"]["name"] == "Cloud Infrastructure"
    assert data["data"]["slug"] == "cloud-infrastructure"
    assert data["data"]["repositories_count"] == 0


def test_create_workspace_validation_errors(client):
    # Non-json
    res = client.post("/api/workspaces/", data="not json", content_type="text/plain")
    assert res.status_code == 400

    # Missing name
    res = client.post(
        "/api/workspaces/",
        data=json.dumps({"slug": "missing-name"}),
        content_type="application/json",
    )
    assert res.status_code == 400
    assert "Fields 'name' and 'slug' are required." in res.get_json()["error"]

    # Empty name
    res = client.post(
        "/api/workspaces/",
        data=json.dumps({"name": "   ", "slug": "valid-slug"}),
        content_type="application/json",
    )
    assert res.status_code == 400
    assert "cannot be empty" in res.get_json()["error"]

    # Non-string slug
    res = client.post(
        "/api/workspaces/",
        data=json.dumps({"name": "Valid", "slug": 123}),
        content_type="application/json",
    )
    assert res.status_code == 400


def test_create_workspace_duplicate_slug_returns_409(client):
    payload = {"name": "Workspace 1", "slug": "dup-ws"}
    res1 = client.post("/api/workspaces/", data=json.dumps(payload), content_type="application/json")
    assert res1.status_code == 201

    res2 = client.post("/api/workspaces/", data=json.dumps({"name": "Workspace 2", "slug": "dup-ws"}), content_type="application/json")
    assert res2.status_code == 409
    assert "already exists" in res2.get_json()["error"]


def test_get_workspace_by_slug_found_and_not_found(client):
    client.post("/api/workspaces/", data=json.dumps({"name": "Core WS", "slug": "core-ws"}), content_type="application/json")

    res = client.get("/api/workspaces/core-ws")
    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "Core WS"
    assert "repositories" in data

    res_404 = client.get("/api/workspaces/missing-ws")
    assert res_404.status_code == 404


def test_update_workspace_success_and_errors(client):
    client.post("/api/workspaces/", data=json.dumps({"name": "Initial WS", "slug": "initial-ws"}), content_type="application/json")

    # Successful update
    res = client.put(
        "/api/workspaces/initial-ws",
        data=json.dumps({"name": "Renamed WS", "slug": "renamed-ws", "description": "Updated desc"}),
        content_type="application/json",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["data"]["name"] == "Renamed WS"
    assert data["data"]["slug"] == "renamed-ws"

    # Non-json
    res = client.put("/api/workspaces/renamed-ws", data="text", content_type="text/plain")
    assert res.status_code == 400

    # 404 update
    res = client.put("/api/workspaces/missing-ws", data=json.dumps({"name": "New"}), content_type="application/json")
    assert res.status_code == 404


def test_delete_workspace(client):
    client.post("/api/workspaces/", data=json.dumps({"name": "Delete WS", "slug": "delete-ws"}), content_type="application/json")

    res = client.delete("/api/workspaces/delete-ws")
    assert res.status_code == 200
    assert "deleted successfully" in res.get_json()["message"]

    res_404 = client.delete("/api/workspaces/delete-ws")
    assert res_404.status_code == 404


def test_link_and_unlink_repository_endpoint(client):
    # Create workspace and repository
    client.post("/api/workspaces/", data=json.dumps({"name": "Dev WS", "slug": "dev-ws"}), content_type="application/json")
    client.post("/api/repositories/", data=json.dumps({"name": "Dev Repo", "slug": "dev-repo"}), content_type="application/json")

    # Link repo
    res = client.post(
        "/api/workspaces/dev-ws/repositories",
        data=json.dumps({"repository_slug": "dev-repo"}),
        content_type="application/json",
    )
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["data"]["repositories"]) == 1
    assert data["data"]["repositories"][0]["slug"] == "dev-repo"

    # Unlink repo
    res = client.delete("/api/workspaces/dev-ws/repositories/dev-repo")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["data"]["repositories"]) == 0
