import sqlite3
import pytest
from migrations import run_migration_001 as run_migration


def test_migration_adds_column_and_preserves_data():
    # Set up an in-memory database with the old schema
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            slug VARCHAR(200) UNIQUE NOT NULL,
            summary TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Insert test data prior to migration
    cursor.execute("""
        INSERT INTO concepts (title, slug, summary, status, created_at)
        VALUES ('Legacy Concept', 'legacy-concept', 'Created before migration', 'DRAFT', '2026-07-27 12:00:00');
    """)
    conn.commit()

    # Verify updated_at is NOT in columns initially
    cursor.execute("PRAGMA table_info(concepts);")
    cols_before = [row[1] for row in cursor.fetchall()]
    assert "updated_at" not in cols_before

    # Run migration
    success, msg = run_migration(connection=conn)
    assert success is True
    assert "Successfully added" in msg

    # Verify updated_at column now exists
    cursor.execute("PRAGMA table_info(concepts);")
    cols_after = [row[1] for row in cursor.fetchall()]
    assert "updated_at" in cols_after

    # Verify existing record was preserved and backfilled
    cursor.execute("SELECT id, title, slug, summary, status, created_at, updated_at FROM concepts WHERE slug='legacy-concept';")
    row = cursor.fetchone()
    assert row is not None
    assert row[1] == "Legacy Concept"
    assert row[2] == "legacy-concept"
    assert row[3] == "Created before migration"
    assert row[4] == "DRAFT"
    assert row[5] == "2026-07-27 12:00:00"
    # updated_at was backfilled with created_at value
    assert row[6] == "2026-07-27 12:00:00"

    # Test idempotency: run migration a second time
    success2, msg2 = run_migration(connection=conn)
    assert success2 is True
    assert "already exists" in msg2

    conn.close()
