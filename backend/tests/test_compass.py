"""Tests for Phase 5 — Forge Compass recommendation engine and persistence."""

import json
import pytest


def test_compass_empty_platform_generates_no_fake_recommendations(client):
    res = client.get("/api/compass/")
    assert res.status_code == 200
    data = res.get_json()
    assert data["recommendations"] == []
    assert data["counts"]["active_pending"] == 0


def test_compass_generates_evidence_backed_recommendations_and_deduplicates(client):
    # Create an unassigned repository with no concepts -> triggers REPO_NO_CONCEPTS + REPO_NO_WORKSPACE + REPO_MISSING_METADATA
    client.post(
        "/api/repositories/",
        data=json.dumps({"name": "Billing API", "slug": "billing-api"}),
        content_type="application/json",
    )

    res1 = client.get("/api/compass/")
    assert res1.status_code == 200
    data1 = res1.get_json()
    rules1 = {r["rule_code"] for r in data1["groups"]["active_pending"]}
    assert "REPO_NO_CONCEPTS" in rules1
    assert "REPO_NO_WORKSPACE" in rules1
    assert "REPO_MISSING_METADATA" in rules1

    # Verify supporting evidence references real repo slug
    no_concepts_rec = next(r for r in data1["groups"]["active_pending"] if r["rule_code"] == "REPO_NO_CONCEPTS")
    assert no_concepts_rec["priority"] == "HIGH"
    assert no_concepts_rec["evidence"]["repository_slug"] == "billing-api"
    assert no_concepts_rec["evidence"]["concept_count"] == 0

    count_before = len(data1["recommendations"])

    # Refreshing repeatedly must NEVER create duplicates
    res2 = client.post("/api/compass/refresh")
    assert res2.status_code == 200
    assert len(res2.get_json()["recommendations"]) == count_before


def test_compass_completion_dismissal_and_refresh_preservation(client):
    client.post(
        "/api/repositories/",
        data=json.dumps({"name": "Gateway", "slug": "gateway"}),
        content_type="application/json",
    )

    recs = client.get("/api/compass/").get_json()["groups"]["active_pending"]
    rec_complete = next(r for r in recs if r["rule_code"] == "REPO_NO_CONCEPTS")
    rec_dismiss = next(r for r in recs if r["rule_code"] == "REPO_NO_WORKSPACE")

    # Complete one, Dismiss one
    c_res = client.patch(
        f"/api/compass/recommendations/{rec_complete['id']}",
        data=json.dumps({"status": "COMPLETED"}),
        content_type="application/json",
    )
    assert c_res.status_code == 200
    assert c_res.get_json()["data"]["status"] == "COMPLETED"
    assert c_res.get_json()["data"]["resolved_at"] is not None

    d_res = client.patch(
        f"/api/compass/recommendations/{rec_dismiss['id']}",
        data=json.dumps({"status": "DISMISSED"}),
        content_type="application/json",
    )
    assert d_res.status_code == 200
    assert d_res.get_json()["data"]["status"] == "DISMISSED"

    # Refreshing when underlying condition STILL holds must NOT overwrite user decisions!
    refreshed = client.post("/api/compass/refresh").get_json()
    assert any(r["id"] == rec_complete["id"] and r["status"] == "COMPLETED" for r in refreshed["groups"]["completed"])
    assert any(r["id"] == rec_dismiss["id"] and r["status"] == "DISMISSED" for r in refreshed["groups"]["dismissed"])

    # Reopening restores PENDING
    reopen = client.patch(
        f"/api/compass/recommendations/{rec_dismiss['id']}",
        data=json.dumps({"status": "PENDING"}),
        content_type="application/json",
    )
    assert reopen.status_code == 200
    assert reopen.get_json()["data"]["status"] == "PENDING"
    assert reopen.get_json()["data"]["resolved_at"] is None


def test_compass_distinguishes_resolved_in_data_from_completed(client):
    ws = client.post(
        "/api/workspaces/",
        data=json.dumps({"name": "Core", "slug": "core"}),
        content_type="application/json",
    ).get_json()["data"]

    repo = client.post(
        "/api/repositories/",
        data=json.dumps({
            "name": "Payment Service",
            "slug": "payment-service",
            "description": "Handles ledger and payouts",
            "vcs_url": "https://github.com/forge/payments",
            "primary_language": "Go",
            "workspace_ids": [ws["id"]],
        }),
        content_type="application/json",
    ).get_json()["data"]

    initial = client.get("/api/compass/").get_json()
    no_concepts = next(r for r in initial["groups"]["active_pending"] if r["rule_code"] == "REPO_NO_CONCEPTS")

    # Link a substantive concept to payment-service -> REPO_NO_CONCEPTS condition no longer triggers
    client.post(
        "/api/concepts/",
        data=json.dumps({
            "title": "Double-Entry Ledger",
            "slug": "double-entry-ledger",
            "summary": "Immutable credit and debit accounting entries.",
            "content": "## Accounting Invariants\nEvery transaction sums to zero across accounts.",
            "tags": ["fintech", "ledger"],
            "category": "data",
            "repository_ids": [repo["id"]],
        }),
        content_type="application/json",
    )

    after = client.get("/api/compass/").get_json()
    # Must NOT be marked COMPLETED automatically — moves to no_longer_relevant (status=PENDING, is_active=False)
    assert after["groups"]["completed"] == []
    assert any(
        r["id"] == no_concepts["id"] and r["status"] == "PENDING" and r["is_active"] is False
        for r in after["groups"]["no_longer_relevant"]
    )
    # Now REPO_LOW_COVERAGE fires honestly (1/5 concepts)
    assert any(r["rule_code"] == "REPO_LOW_COVERAGE" for r in after["groups"]["active_pending"])


def test_compass_handles_unconnected_concepts_and_deleted_entity(client):
    ws = client.post(
        "/api/workspaces/",
        data=json.dumps({"name": "Core", "slug": "core"}),
        content_type="application/json",
    ).get_json()["data"]
    repo = client.post(
        "/api/repositories/",
        data=json.dumps({"name": "Search", "slug": "search", "workspace_ids": [ws["id"]]}),
        content_type="application/json",
    ).get_json()["data"]
    client.post(
        "/api/concepts/",
        data=json.dumps({
            "title": "Inverted Index",
            "slug": "inverted-index",
            "summary": "Mapping terms to document postings lists.",
            "content": "## Structure\nUsed in full-text search engines for fast term lookup.",
            "tags": ["search"],
            "repository_ids": [repo["id"]],
        }),
        content_type="application/json",
    )
    client.post(
        "/api/concepts/",
        data=json.dumps({
            "title": "BM25 Ranking",
            "slug": "bm25-ranking",
            "summary": "Probabilistic relevance scoring formula.",
            "content": "## Formula\nBalances term frequency saturation and document length normalization.",
            "tags": ["ranking"],
            "repository_ids": [repo["id"]],
        }),
        content_type="application/json",
    )

    recs = client.get("/api/compass/").get_json()["groups"]["active_pending"]
    unconnected_rec = next((r for r in recs if r["rule_code"] == "REPO_UNCONNECTED_CONCEPTS"), None)
    assert unconnected_rec is not None
    assert unconnected_rec["evidence"]["concept_count"] == 2
    assert unconnected_rec["evidence"]["connected_concepts"] == 0

    # Delete repository -> Compass refresh marks related recs inactive and clears stale entity_id
    del_res = client.delete("/api/repositories/search")
    assert del_res.status_code == 200

    after_del = client.get("/api/compass/").get_json()
    stale = next(r for r in after_del["recommendations"] if r["id"] == unconnected_rec["id"])
    assert stale["is_active"] is False
    assert stale["entity_id"] is None


def test_compass_validation_errors(client):
    assert client.get("/api/compass/?status=BOGUS").status_code == 400
    assert client.get("/api/compass/?priority=CRITICAL").status_code == 400
    assert client.patch("/api/compass/recommendations/999", data=json.dumps({"status": "COMPLETED"}), content_type="application/json").status_code == 404
    assert client.patch("/api/compass/recommendations/1", data="not json", content_type="text/plain").status_code == 400
