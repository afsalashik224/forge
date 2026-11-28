"""Tests for Phase 5 — Progress Engine metrics, gaps, and API endpoints."""

import json
import pytest


def test_progress_empty_platform_honest_state(client):
    res = client.get("/api/progress/")
    assert res.status_code == 200
    data = res.get_json()
    overview = data["overview"]
    assert overview["total_repositories"] == 0
    assert overview["total_concepts"] == 0
    assert overview["average_documentation_score"] is None
    assert overview["has_sufficient_data"] is False
    assert data["repositories"] == []


def test_progress_repository_with_no_concepts(app, repo_service, workspace_service, progress_service):
    ws = workspace_service.create_workspace(name="Core", slug="core")
    repo_service.create_repository(
        name="Empty Service",
        slug="empty-service",
        description="No concepts linked yet",
        vcs_url="https://github.com/forge/empty",
        primary_language="Python",
        workspace_ids=[ws.id],
    )

    detail = progress_service.get_repository_progress("empty-service")["repository"]
    assert detail["data_sufficiency"] == "NO_CONCEPTS"
    assert detail["counts"]["concepts"] == 0
    assert detail["dimensions"]["knowledge_coverage"]["score"] == 0.0
    assert detail["dimensions"]["documentation_completeness"]["score"] == 0.0
    assert detail["dimensions"]["concept_diversity"]["score"] == 0.0
    assert detail["dimensions"]["relationship_coverage"]["score"] == 0.0
    # 4/4 metadata checks passed -> organization_quality == 100.0
    assert detail["dimensions"]["organization_quality"]["score"] == 100.0
    # Weighted score: 0.15 * 100 = 15.0
    assert detail["documentation_score"] == 15.0
    assert "No knowledge concepts linked to this repository." in detail["gaps"]


def test_progress_metrics_multiple_workspaces_concepts_and_updates(
    app, repo_service, workspace_service, service, graph_service, progress_service
):
    ws1 = workspace_service.create_workspace(name="Platform", slug="platform")
    ws2 = workspace_service.create_workspace(name="Security", slug="security")
    repo = repo_service.create_repository(
        name="Auth API",
        slug="auth-api",
        description="Central authentication API gateway",
        vcs_url="https://github.com/forge/auth-api",
        primary_language="Python",
        workspace_ids=[ws1.id, ws2.id],
    )

    c1 = service.create_concept(
        title="Zero Trust",
        slug="zero-trust",
        summary="Never trust, always verify security posture.",
        content="## Architecture\nDetailed implementation notes for mTLS and strict token validation.",
        tags=["security", "mtls"],
        category="security",
        repository_ids=[repo.id],
    )
    service.update_concept("zero-trust", status="PUBLISHED")

    c2 = service.create_concept(
        title="JWT Signing",
        slug="jwt-signing",
        summary="Short summary.",
        content="",  # missing substantive content
        tags=[],
        category="architecture",
        repository_ids=[repo.id],
    )

    # Before linking c1 <-> c2
    before = progress_service.get_repository_progress("auth-api")["repository"]
    assert before["counts"]["workspaces"] == 2
    assert before["counts"]["concepts"] == 2
    assert before["counts"]["published_concepts"] == 1
    assert before["counts"]["connected_concepts"] == 0
    assert before["dimensions"]["knowledge_coverage"]["score"] == 40.0  # 2/5
    # c1 passes 4/4, c2 passes 0/4 (summary len 14 < 15, no content, no tags, DRAFT) -> 4/8 = 50%
    assert before["dimensions"]["documentation_completeness"]["score"] == 50.0
    assert before["dimensions"]["relationship_coverage"]["score"] == 0.0
    # Diversity: 2/3 categories (0.6 * 2/3 = 0.4) + 2/4 tags (0.4 * 0.5 = 0.2) = 60.0
    assert before["dimensions"]["concept_diversity"]["score"] == 60.0

    # Add graph relationship between c1 and c2 + enrich c2
    rel = graph_service.create_relationship(
        source_concept_id=c1.id,
        target_concept_id=c2.id,
        relationship_type="DEPENDS_ON",
    )
    service.update_concept(
        "jwt-signing",
        summary="Asymmetric RS256 JSON Web Token signing strategy.",
        content="## Key Rotation\nRotate public JWKS endpoints cleanly with key IDs.",
        tags=["jwt", "crypto"],
        status="PUBLISHED",
    )

    after = progress_service.get_repository_progress("auth-api")["repository"]
    assert after["counts"]["connected_concepts"] == 2
    assert after["counts"]["internal_edges"] == 1
    assert after["dimensions"]["relationship_coverage"]["score"] == 100.0
    assert after["dimensions"]["documentation_completeness"]["score"] == 100.0
    assert after["documentation_score"] > before["documentation_score"]

    # Deleting the relationship cleanly reduces relationship coverage back to 0%
    graph_service.delete_relationship(rel.id)
    after_delete = progress_service.get_repository_progress("auth-api")["repository"]
    assert after_delete["counts"]["connected_concepts"] == 0
    assert after_delete["dimensions"]["relationship_coverage"]["score"] == 0.0


def test_progress_api_endpoints_and_404(client):
    res_404 = client.get("/api/progress/repositories/missing-repo")
    assert res_404.status_code == 404

    client.post(
        "/api/repositories/",
        data=json.dumps({"name": "Worker", "slug": "worker"}),
        content_type="application/json",
    )

    overview = client.get("/api/progress/")
    assert overview.status_code == 200
    body = overview.get_json()
    assert body["overview"]["total_repositories"] == 1
    assert len(body["metric_definitions"]) == 5

    detail = client.get("/api/progress/repositories/worker")
    assert detail.status_code == 200
    assert detail.get_json()["repository"]["slug"] == "worker"
