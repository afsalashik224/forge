"""
Standalone Phase 0 verification runner.
Runs using Python standard library to verify all backend logic,
models, service, API endpoints, error handling, and migrations.
"""

import json
import os
import sqlite3
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database.db import db
from app.models.concept import Concept
from app.repositories.concept_repository import ConceptRepository
from app.services.concept_service import ConceptService
from migrations import run_migration_001 as run_migration


def run_checks():
    results = []

    def check(name, fn):
        try:
            fn()
            results.append((name, "PASSED", None))
            print(f"  [PASSED] {name}")
        except Exception as e:
            results.append((name, "FAILED", str(e)))
            print(f"  [FAILED] {name}: {e}")

    print("\n=== Running Phase 0 Verification Checks ===")

    # 1. App initialization
    def test_app_init():
        app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
        assert app is not None
        assert app.config["TESTING"] is True
    check("Application Factory Initialization", test_app_init)

    # 2. Migration safety & idempotency
    def test_migration_safety():
        conn = sqlite3.connect(":memory:")
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                slug VARCHAR(200) UNIQUE NOT NULL,
                summary TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            INSERT INTO concepts (title, slug, summary, status, created_at)
            VALUES ('Prior Concept', 'prior-concept', 'Initial note', 'DRAFT', '2026-07-27 10:00:00');
        """)
        conn.commit()

        # Step A: Run migration
        success, msg = run_migration(connection=conn)
        assert success is True, msg

        # Step B: Check column exists
        cur.execute("PRAGMA table_info(concepts);")
        columns = [row[1] for row in cur.fetchall()]
        assert "updated_at" in columns, "updated_at column was not added"

        # Step C: Check backfill
        cur.execute("SELECT created_at, updated_at FROM concepts WHERE slug='prior-concept';")
        row = cur.fetchone()
        assert row[0] == "2026-07-27 10:00:00"
        assert row[1] == "2026-07-27 10:00:00", f"Backfill failed: {row}"

        # Step D: Test idempotency
        success2, msg2 = run_migration(connection=conn)
        assert success2 is True, msg2
        assert "already exists" in msg2

        conn.close()
    check("Migration Safety, Backfill, and Idempotency", test_migration_safety)

    # Setup isolated test app context for ORM, Service & API tests
    test_app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "test-key"
    })

    with test_app.app_context():
        db.create_all()

        # 3. Repository & Model Timestamp semantics
        def test_timestamps():
            repo = ConceptRepository()
            c = Concept(title="Timestamp Check", slug="ts-check", summary="Testing timestamps")
            saved = repo.create(c)
            assert saved.created_at is not None
            c_id = saved.id
            first_created = saved.created_at

            # Update concept
            saved.summary = "New summary"
            db.session.commit()

            reloaded = repo.get_by_id(c_id)
            assert reloaded.created_at == first_created
            assert reloaded.summary == "New summary"
        check("Timestamp Immutability on created_at", test_timestamps)

        # 4. Service layer duplicate rejection
        def test_service():
            repo = ConceptRepository()
            svc = ConceptService(repository=repo)
            c1 = svc.create_concept("Microservices", "microservices", "Architecture pattern")
            assert c1.id is not None

            # Duplicate slug must raise ValueError
            try:
                svc.create_concept("Microservices 2", "microservices", "Duplicate")
                raise AssertionError("Expected ValueError on duplicate slug")
            except ValueError as ve:
                assert "already exists" in str(ve)

            # Retrieval
            assert svc.get_concept_by_slug("microservices") is not None
            assert svc.get_concept_by_slug("nonexistent") is None
        check("Service Business Logic & Duplicate Rejection", test_service)

    # 5. API Endpoints and Error Handling
    client = test_app.test_client()

    def test_api():
        # Health check
        res = client.get("/health")
        assert res.status_code == 200
        assert res.get_json()["status"] == "healthy"

        # Non-JSON payload returns 400
        res = client.post("/api/concepts/", data="not json", content_type="text/plain")
        assert res.status_code == 400
        assert "error" in res.get_json()

        # Missing required fields returns 400
        res = client.post(
            "/api/concepts/",
            data=json.dumps({"summary": "no title or slug"}),
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "error" in res.get_json()

        # Empty string title returns 400
        res = client.post(
            "/api/concepts/",
            data=json.dumps({"title": "   ", "slug": "valid-slug"}),
            content_type="application/json"
        )
        assert res.status_code == 400
        assert "error" in res.get_json()

        # Valid creation returns 201
        res = client.post(
            "/api/concepts/",
            data=json.dumps({"title": "Event Sourcing", "slug": "event-sourcing", "summary": "Store events"}),
            content_type="application/json"
        )
        assert res.status_code == 201
        data = res.get_json()
        assert data["data"]["slug"] == "event-sourcing"
        assert "created_at" in data["data"]

        # Duplicate slug returns 409
        res = client.post(
            "/api/concepts/",
            data=json.dumps({"title": "Event Sourcing", "slug": "event-sourcing", "summary": "Duplicate"}),
            content_type="application/json"
        )
        assert res.status_code == 409
        assert "error" in res.get_json()
        assert "already exists" in res.get_json()["error"]

        # 404 for unknown slug
        res = client.get("/api/concepts/unknown-slug")
        assert res.status_code == 404
        assert "error" in res.get_json()

        # 200 for existing slug
        res = client.get("/api/concepts/event-sourcing")
        assert res.status_code == 200
        assert res.get_json()["slug"] == "event-sourcing"

        # List concepts returns list
        res = client.get("/api/concepts/")
        assert res.status_code == 200
        assert isinstance(res.get_json(), list)
        assert len(res.get_json()) >= 1
    check("API Endpoints & Status Codes (200, 201, 400, 404, 409)", test_api)

    # 6. Global error handlers (e.g. 404 on undefined route, 405 on wrong method)
    def test_global_error_handlers():
        res = client.get("/undefined-route-xyz")
        assert res.status_code == 404
        assert "error" in res.get_json()

        res = client.delete("/health")
        assert res.status_code == 405
        assert "error" in res.get_json()
    check("Global Flask Error Handlers (404, 405)", test_global_error_handlers)

    print("\n=== Verification Summary ===")
    all_passed = all(status == "PASSED" for _, status, _ in results)
    print(f"Total checks: {len(results)} | Passed: {sum(1 for _, s, _ in results if s == 'PASSED')} | Failed: {sum(1 for _, s, _ in results if s == 'FAILED')}")
    return all_passed


if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
