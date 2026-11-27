"""Tests for Phase 3 — Rich Knowledge Authoring (content, tags, category, search)."""

import json
import pytest


def test_create_concept_with_content_tags_category(client):
    payload = {
        "title": "Event Sourcing",
        "slug": "event-sourcing",
        "summary": "Persist state as a sequence of events.",
        "content": "## Overview\n\nEvent sourcing stores all changes to application state as a **sequence of events**.\n\n```python\nclass Event:\n    def __init__(self, type, data):\n        self.type = type\n        self.data = data\n```",
        "tags": ["cqrs", "ddd", "architecture"],
        "category": "architecture",
    }
    res = client.post(
        "/api/concepts/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["title"] == "Event Sourcing"
    assert data["content"].startswith("## Overview")
    assert data["tags"] == ["cqrs", "ddd", "architecture"]
    assert data["category"] == "architecture"


def test_create_concept_without_new_fields_uses_defaults(client):
    payload = {"title": "Simple Concept", "slug": "simple-concept", "summary": "No extras."}
    res = client.post(
        "/api/concepts/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["content"] == ""
    assert data["tags"] == []
    assert data["category"] == ""


def test_get_concept_returns_new_fields(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({
            "title": "CQRS Pattern",
            "slug": "cqrs-pattern",
            "summary": "Command Query Responsibility Segregation",
            "content": "# CQRS\nSeparate reads and writes.",
            "tags": ["patterns", "architecture"],
            "category": "design-patterns",
        }),
        content_type="application/json",
    )

    res = client.get("/api/concepts/cqrs-pattern")
    assert res.status_code == 200
    data = res.get_json()
    assert data["content"] == "# CQRS\nSeparate reads and writes."
    assert data["tags"] == ["patterns", "architecture"]
    assert data["category"] == "design-patterns"


def test_get_concepts_list_includes_tags_and_category(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({
            "title": "Redis Caching",
            "slug": "redis-caching",
            "summary": "In-memory data store",
            "tags": ["redis", "caching"],
            "category": "performance",
        }),
        content_type="application/json",
    )

    res = client.get("/api/concepts/")
    assert res.status_code == 200
    concepts = res.get_json()
    assert len(concepts) >= 1
    redis = next((c for c in concepts if c["slug"] == "redis-caching"), None)
    assert redis is not None
    assert redis["tags"] == ["redis", "caching"]
    assert redis["category"] == "performance"


def test_update_concept_with_new_fields(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({
            "title": "API Gateway",
            "slug": "api-gateway",
            "summary": "Reverse proxy for APIs",
        }),
        content_type="application/json",
    )

    res = client.put(
        "/api/concepts/api-gateway",
        data=json.dumps({
            "title": "API Gateway",
            "slug": "api-gateway",
            "content": "# API Gateway\n\nAn API gateway sits in front of microservices.",
            "tags": ["microservices", "api", "gateway"],
            "category": "infrastructure",
        }),
        content_type="application/json",
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "API gateway sits in front" in data["content"]
    assert data["tags"] == ["microservices", "api", "gateway"]
    assert data["category"] == "infrastructure"


def test_update_concept_omitted_new_fields_preserves_existing(client):
    client.post(
        "/api/concepts/",
        data=json.dumps({
            "title": "Circuit Breaker",
            "slug": "circuit-breaker",
            "summary": "Fault tolerance pattern",
            "content": "# Circuit Breaker\nPrevents cascading failures.",
            "tags": ["resilience", "patterns"],
            "category": "architecture",
        }),
        content_type="application/json",
    )

    # Update only title — content, tags, category should be preserved
    res = client.put(
        "/api/concepts/circuit-breaker",
        data=json.dumps({
            "title": "Circuit Breaker Pattern",
            "slug": "circuit-breaker",
        }),
        content_type="application/json",
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["title"] == "Circuit Breaker Pattern"
    assert data["content"] == "# Circuit Breaker\nPrevents cascading failures."
    assert data["tags"] == ["resilience", "patterns"]
    assert data["category"] == "architecture"


def test_search_concepts_by_text_query(client):
    client.post("/api/concepts/", data=json.dumps({
        "title": "Load Balancing", "slug": "load-balancing",
        "summary": "Distribute traffic across servers",
        "content": "Round-robin, least connections, and weighted algorithms.",
        "tags": ["networking"],
        "category": "infrastructure",
    }), content_type="application/json")

    client.post("/api/concepts/", data=json.dumps({
        "title": "Database Sharding", "slug": "db-sharding",
        "summary": "Horizontal data partitioning",
        "tags": ["database", "scaling"],
        "category": "data",
    }), content_type="application/json")

    # Search for "traffic" — should find load balancing
    res = client.get("/api/concepts/?q=traffic")
    assert res.status_code == 200
    results = res.get_json()
    slugs = {c["slug"] for c in results}
    assert "load-balancing" in slugs
    assert "db-sharding" not in slugs


def test_search_concepts_by_tag_filter(client):
    client.post("/api/concepts/", data=json.dumps({
        "title": "JWT Auth", "slug": "jwt-auth",
        "summary": "JSON Web Token authentication",
        "tags": ["auth", "security", "jwt"],
    }), content_type="application/json")

    client.post("/api/concepts/", data=json.dumps({
        "title": "OAuth 2.0", "slug": "oauth-2",
        "summary": "Authorization framework",
        "tags": ["auth", "oauth"],
    }), content_type="application/json")

    # Filter by tag "jwt"
    res = client.get("/api/concepts/?tags=jwt")
    assert res.status_code == 200
    results = res.get_json()
    slugs = {c["slug"] for c in results}
    assert "jwt-auth" in slugs
    assert "oauth-2" not in slugs


def test_search_concepts_by_category_filter(client):
    client.post("/api/concepts/", data=json.dumps({
        "title": "TLS/SSL", "slug": "tls-ssl",
        "summary": "Transport Layer Security",
        "category": "security",
    }), content_type="application/json")

    client.post("/api/concepts/", data=json.dumps({
        "title": "Docker Compose", "slug": "docker-compose",
        "summary": "Multi-container orchestration",
        "category": "devops",
    }), content_type="application/json")

    # Filter by category "security"
    res = client.get("/api/concepts/?category=security")
    assert res.status_code == 200
    results = res.get_json()
    slugs = {c["slug"] for c in results}
    assert "tls-ssl" in slugs
    assert "docker-compose" not in slugs


def test_search_concepts_by_status_filter(client):
    client.post("/api/concepts/", data=json.dumps({
        "title": "Published One", "slug": "published-one", "summary": "P1",
    }), content_type="application/json")
    # Update to PUBLISHED
    client.put("/api/concepts/published-one", data=json.dumps({
        "title": "Published One", "slug": "published-one", "status": "PUBLISHED",
    }), content_type="application/json")

    client.post("/api/concepts/", data=json.dumps({
        "title": "Draft One", "slug": "draft-one", "summary": "D1",
    }), content_type="application/json")

    res = client.get("/api/concepts/?status=PUBLISHED")
    assert res.status_code == 200
    results = res.get_json()
    slugs = {c["slug"] for c in results}
    assert "published-one" in slugs
    assert "draft-one" not in slugs


def test_search_concepts_combined_filters(client):
    client.post("/api/concepts/", data=json.dumps({
        "title": "Kubernetes Networking", "slug": "k8s-networking",
        "summary": "CNI plugins and service mesh",
        "tags": ["kubernetes", "networking"],
        "category": "infrastructure",
    }), content_type="application/json")

    client.post("/api/concepts/", data=json.dumps({
        "title": "Kubernetes Security", "slug": "k8s-security",
        "summary": "RBAC and pod security policies",
        "tags": ["kubernetes", "security"],
        "category": "security",
    }), content_type="application/json")

    # Combine: tag=kubernetes + category=security
    res = client.get("/api/concepts/?tags=kubernetes&category=security")
    assert res.status_code == 200
    results = res.get_json()
    slugs = {c["slug"] for c in results}
    assert "k8s-security" in slugs
    assert "k8s-networking" not in slugs


def test_tags_validation_rejects_non_list(client):
    res = client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Bad Tags", "slug": "bad-tags", "tags": "not-a-list"}),
        content_type="application/json",
    )
    assert res.status_code == 400
    assert "list" in res.get_json()["error"].lower()


def test_content_validation_rejects_non_string(client):
    res = client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Bad Content", "slug": "bad-content", "content": 123}),
        content_type="application/json",
    )
    assert res.status_code == 400
    assert "string" in res.get_json()["error"].lower()


def test_concept_create_and_update_with_repository_associations_and_filter(client):
    # Create workspace and two repositories
    ws_res = client.post(
        "/api/workspaces/",
        data=json.dumps({"name": "Platform", "slug": "platform"}),
        content_type="application/json",
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.get_json()["data"]["id"]

    repo1_res = client.post(
        "/api/repositories/",
        data=json.dumps({"name": "Auth Service", "slug": "auth-service", "workspace_ids": [ws_id]}),
        content_type="application/json",
    )
    assert repo1_res.status_code == 201
    repo1_id = repo1_res.get_json()["data"]["id"]

    repo2_res = client.post(
        "/api/repositories/",
        data=json.dumps({"name": "Gateway", "slug": "gateway"}),
        content_type="application/json",
    )
    assert repo2_res.status_code == 201
    repo2_id = repo2_res.get_json()["data"]["id"]

    # Create concept linked to repo1
    c_res = client.post(
        "/api/concepts/",
        data=json.dumps({
            "title": "Zero Trust Auth",
            "slug": "zero-trust-auth",
            "summary": "Mutual TLS and JWTs",
            "content": "# Zero Trust\nVerify explicitly.",
            "tags": ["security"],
            "category": "security",
            "repository_ids": [repo1_id],
        }),
        content_type="application/json",
    )
    assert c_res.status_code == 201
    c_data = c_res.get_json()["data"]
    assert c_data["repositories_count"] == 1
    assert c_data["repositories"][0]["slug"] == "auth-service"
    assert c_data["workspaces"][0]["slug"] == "platform"

    # Filter by repository and workspace
    by_repo = client.get("/api/concepts/?repository=auth-service").get_json()
    assert [c["slug"] for c in by_repo] == ["zero-trust-auth"]

    by_ws = client.get("/api/concepts/?workspace=platform").get_json()
    assert [c["slug"] for c in by_ws] == ["zero-trust-auth"]

    by_other_repo = client.get("/api/concepts/?repository=gateway").get_json()
    assert by_other_repo == []

    # Update concept to link repo2 instead of repo1
    u_res = client.put(
        "/api/concepts/zero-trust-auth",
        data=json.dumps({
            "title": "Zero Trust Auth",
            "slug": "zero-trust-auth",
            "repository_ids": [repo2_id],
        }),
        content_type="application/json",
    )
    assert u_res.status_code == 200
    u_data = u_res.get_json()["data"]
    assert [r["slug"] for r in u_data["repositories"]] == ["gateway"]
    assert u_data["workspaces"] == []
    # Omitted content, tags, category preserved
    assert u_data["content"] == "# Zero Trust\nVerify explicitly."
    assert u_data["tags"] == ["security"]
    assert u_data["category"] == "security"


def test_repository_ids_validation_rejects_non_list(client):
    res = client.post(
        "/api/concepts/",
        data=json.dumps({"title": "Bad Repos", "slug": "bad-repos", "repository_ids": "not-a-list"}),
        content_type="application/json",
    )
    assert res.status_code == 400
    assert "list" in res.get_json()["error"].lower()
