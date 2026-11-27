import sqlite3
import pytest
from migrations import run_migration_002 as run_migration


def test_migration_002_creates_tables_and_preserves_concepts():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Pre-existing concepts table
    cursor.execute("""
        CREATE TABLE concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            slug VARCHAR(200) UNIQUE NOT NULL,
            summary TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        INSERT INTO concepts (title, slug, summary, status)
        VALUES ('Core Architecture', 'core-architecture', 'Foundational concepts', 'ACTIVE');
    """)
    conn.commit()

    # Run migration 002
    success, msg = run_migration(connection=conn)
    assert success is True
    assert "Successfully created" in msg

    # Verify tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    assert "workspaces" in tables
    assert "repositories" in tables
    assert "workspace_repositories" in tables
    assert "repository_concepts" in tables

    # Verify existing concept data was preserved
    cursor.execute("SELECT title, slug FROM concepts WHERE slug='core-architecture';")
    concept = cursor.fetchone()
    assert concept is not None
    assert concept[0] == "Core Architecture"

    # Verify idempotency: running migration a second time succeeds without errors
    success2, msg2 = run_migration(connection=conn)
    assert success2 is True
    assert "Successfully created" in msg2

    conn.close()
