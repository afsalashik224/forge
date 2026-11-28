"""Comprehensive unit and API tests for Phase 4 — Knowledge Graph."""

import json
import pytest

from app.services.graph_service import DuplicateRelationshipError


def _seed_sample_topology(client):
    """Create real Workspaces, Repositories, Concepts, and Relationships for graph tests."""
    ws = client.post(
        "/api/workspaces/",
        data=json.dumps({"name": "Platform", "slug": "platform", "description": "Core infra"}),
        content_type="application/json",
    ).get_json()["data"]

    ws2 = client.post(
        "/api/workspaces/",
        data=json.dumps({"name": "Frontend", "slug": "frontend"}),
        content_type="application/json",
    ).get_json()["data"]

    repo = client.post(
        "/api/repositories/",
        data=json.dumps({
            "name": "Auth API",
            "slug": "auth-api",
            "primary_language": "Python",
            "workspace_ids": [ws["id"]],
        }),
        content_type="application/json",
    ).get_json()["data"]

    repo2 = client.post(
        "/api/repositories/",
        data=json.dumps({
            "name": "Web UI",
            "slug": "web-ui",
            "primary_language": "TypeScript",
            "workspace_ids": [ws2["id"]],
        }),
        content_type="application/json",
    ).get_json()["data"]

    c1 = client.post(
        "/api/concepts/",
        data=json.dumps({
            "title": "Zero Trust",
            "slug": "zero-trust",
            "summary": "Never trust, always verify",
            "category": "security",
            "tags": ["auth", "security"],
            "repository_ids": [repo["id"]],
        }),
        content_type="application/json",
    ).get_json()["data"]

    c2 = client.post(
        "/api/concepts/",
        data=json.dumps({
            "title": "JWT Tokens",
            "slug": "jwt-tokens",
            "summary": "Signed stateless claims",
            "category": "security",
            "tags": ["jwt"],
            "repository_ids": [repo["id"]],
        }),
        content_type="application/json",
    ).get_json()["data"]

    c3 = client.post(
        "/api/concepts/",
        data=json.dumps({
            "title": "React SPA",
            "slug": "react-spa",
            "summary": "Single page app",
            "category": "frameworks",
            "repository_ids": [repo2["id"]],
        }),
        content_type="application/json",
    ).get_json()["data"]

    return {"ws": ws, "ws2": ws2, "repo": repo, "repo2": repo2, "c1": c1, "c2": c2, "c3": c3}


def test_graph_empty_initially_has_no_fake_nodes(client):
    res = client.get("/api/graph/")
    assert res.status_code == 200
    data = res.get_json()
    assert data["nodes"] == []
    assert data["edges"] == []
    assert data["stats"]["total_nodes"] == 0
    assert data["stats"]["total_edges"] == 0


def test_relationship_service_validation_and_crud(app, service, graph_service):
    c1 = service.create_concept("A", "a", "Concept A")
    c2 = service.create_concept("B", "b", "Concept B")

    # Self-loop rejected
    with pytest.raises(ValueError):
        graph_service.create_relationship(
            source_concept_id=c1.id,
            target_concept_id=c1.id,
            relationship_type="DEPENDS_ON",
        )

    # Invalid relationship type rejected
    with pytest.raises(ValueError):
        graph_service.create_relationship(
            source_concept_id=c1.id,
            target_concept_id=c2.id,
            relationship_type="BOGUS_TYPE",
        )

    # Nonexistent target raises LookupError
    with pytest.raises(LookupError):
        graph_service.create_relationship(
            source_concept_id=c1.id,
            target_concept_id=9999,
            relationship_type="DEPENDS_ON",
        )

    # Create valid relationship (lowercase input normalized to uppercase)
    rel = graph_service.create_relationship(
        source_concept_id=c1.id,
        target_concept_id=c2.id,
        relationship_type="depends_on",
        description="A depends on B",
    )
    assert rel.id is not None
    assert rel.relationship_type == "DEPENDS_ON"

    # Duplicate exact edge raises DuplicateRelationshipError
    with pytest.raises(DuplicateRelationshipError):
        graph_service.create_relationship(
            source_concept_id=c1.id,
            target_concept_id=c2.id,
            relationship_type="DEPENDS_ON",
        )

    # Different relationship type between same pair is allowed
    rel2 = graph_service.create_relationship(
        source_slug="a",
        target_slug="b",
        relationship_type="RELATES_TO",
    )
    assert rel2.id != rel.id

    # Delete relationship
    deleted = graph_service.delete_relationship(rel.id)
    assert deleted["id"] == rel.id
    assert graph_service.get_relationship_by_id(rel.id) is None


def test_graph_api_builds_real_nodes_and_structural_edges(client):
    seeded = _seed_sample_topology(client)

    res = client.get("/api/graph/")
    assert res.status_code == 200
    graph = res.get_json()

    assert graph["stats"]["total_nodes"] == 7  # 2 ws + 2 repo + 3 concepts
    assert graph["stats"]["counts_by_entity"] == {
        "workspace": 2,
        "repository": 2,
        "concept": 3,
    }
    # 2 ws->repo edges + 3 repo->concept edges = 5 structural edges
    assert graph["stats"]["total_edges"] == 5
    edge_types = {e["relationship_type"] for e in graph["edges"]}
    assert edge_types == {"CONTAINS_REPO", "DOCUMENTS_CONCEPT"}

    # Verify real workspace node
    ws_node = next(n for n in graph["nodes"] if n["id"] == f"workspace:{seeded['ws']['id']}")
    assert ws_node["label"] == "Platform"
    assert ws_node["degree"] == 1


def test_graph_api_relationship_endpoints_and_concept_detail(client):
    seeded = _seed_sample_topology(client)

    # Create relationship via POST /api/graph/relationships
    res = client.post(
        "/api/graph/relationships",
        data=json.dumps({
            "source_slug": "zero-trust",
            "target_slug": "jwt-tokens",
            "relationship_type": "DEPENDS_ON",
            "description": "Token verification relies on JWTs",
        }),
        content_type="application/json",
    )
    assert res.status_code == 201
    rel_data = res.get_json()["data"]
    rel_id = rel_data["id"]
    assert rel_data["relationship_type"] == "DEPENDS_ON"
    assert rel_data["source_slug"] == "zero-trust"
    assert rel_data["target_slug"] == "jwt-tokens"

    # Duplicate returns 409
    dup = client.post(
        "/api/graph/relationships",
        data=json.dumps({
            "source_concept_id": seeded["c1"]["id"],
            "target_concept_id": seeded["c2"]["id"],
            "relationship_type": "DEPENDS_ON",
        }),
        content_type="application/json",
    )
    assert dup.status_code == 409

    # Self-loop returns 400
    self_res = client.post(
        "/api/graph/relationships",
        data=json.dumps({
            "source_slug": "zero-trust",
            "target_slug": "zero-trust",
            "relationship_type": "RELATES_TO",
        }),
        content_type="application/json",
    )
    assert self_res.status_code == 400

    # Invalid type returns 400
    bad_type = client.post(
        "/api/graph/relationships",
        data=json.dumps({
            "source_slug": "zero-trust",
            "target_slug": "jwt-tokens",
            "relationship_type": "NOT_A_VALID_TYPE",
        }),
        content_type="application/json",
    )
    assert bad_type.status_code == 400

    # List relationships
    list_res = client.get("/api/graph/relationships?concept=zero-trust")
    assert list_res.status_code == 200
    rels = list_res.get_json()["relationships"]
    assert len(rels) == 1
    assert rels[0]["id"] == rel_id

    # Verify concept detail exposes connected relationships
    c1_detail = client.get("/api/concepts/zero-trust").get_json()
    assert len(c1_detail["relationships"]["outgoing"]) == 1
    assert c1_detail["relationships"]["outgoing"][0]["concept"]["slug"] == "jwt-tokens"

    c2_detail = client.get("/api/concepts/jwt-tokens").get_json()
    assert len(c2_detail["relationships"]["incoming"]) == 1
    assert c2_detail["relationships"]["incoming"][0]["concept"]["slug"] == "zero-trust"

    # Delete relationship
    del_res = client.delete(f"/api/graph/relationships/{rel_id}")
    assert del_res.status_code == 200
    assert client.delete(f"/api/graph/relationships/{rel_id}").status_code == 404


def test_graph_filtering_and_neighborhood_exploration(client):
    seeded = _seed_sample_topology(client)

    client.post(
        "/api/graph/relationships",
        data=json.dumps({
            "source_slug": "zero-trust",
            "target_slug": "jwt-tokens",
            "relationship_type": "DEPENDS_ON",
        }),
        content_type="application/json",
    )

    # Filter by workspace
    ws_graph = client.get("/api/graph/?workspace=platform").get_json()
    ws_slugs = {n["slug"] for n in ws_graph["nodes"]}
    assert ws_slugs == {"platform", "auth-api", "zero-trust", "jwt-tokens"}

    # Filter by entity_types & relationship_types
    concept_only = client.get("/api/graph/?entity_types=concept&relationship_types=DEPENDS_ON").get_json()
    assert {n["entity_type"] for n in concept_only["nodes"]} == {"concept"}
    assert len(concept_only["edges"]) == 1
    assert concept_only["edges"][0]["relationship_type"] == "DEPENDS_ON"

    # Search with include_neighbors=true
    search_graph = client.get("/api/graph/?q=zero-trust&include_neighbors=true").get_json()
    matched_slugs = {n["slug"] for n in search_graph["nodes"]}
    assert "zero-trust" in matched_slugs
    assert "jwt-tokens" in matched_slugs
    assert "auth-api" in matched_slugs
    assert "react-spa" not in matched_slugs

    # Focus BFS exploration (1-hop from zero-trust)
    focus_graph = client.get("/api/graph/?focus=concept:zero-trust&depth=1").get_json()
    focus_slugs = {n["slug"] for n in focus_graph["nodes"]}
    assert focus_slugs == {"zero-trust", "jwt-tokens", "auth-api"}

    # Dedicated neighbors endpoint
    neigh_res = client.get(f"/api/graph/nodes/concept/{seeded['c1']['slug']}/neighbors?depth=1")
    assert neigh_res.status_code == 200
    neigh_data = neigh_res.get_json()
    assert neigh_data["node"]["slug"] == "zero-trust"
    assert len(neigh_data["outgoing"]) == 1
    assert len(neigh_data["incoming"]) == 1  # from repo DOCUMENTS_CONCEPT


def test_deleting_concept_cascades_relationships(client):
    _seed_sample_topology(client)
    client.post(
        "/api/graph/relationships",
        data=json.dumps({
            "source_slug": "zero-trust",
            "target_slug": "jwt-tokens",
            "relationship_type": "DEPENDS_ON",
        }),
        content_type="application/json",
    )

    # Delete concept zero-trust
    del_res = client.delete("/api/concepts/zero-trust")
    assert del_res.status_code == 200

    # Relationship should also be removed cleanly
    rels = client.get("/api/graph/relationships").get_json()["relationships"]
    assert rels == []
