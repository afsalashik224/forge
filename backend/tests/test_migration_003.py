import sqlite3
import pytest
from migrations import run_migration_003 as run_migration


def test_migration_003_adds_columns():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Pre-existing concepts table (after migration 001)
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
        VALUES ('Existing Concept', 'existing-concept', 'Already exists.', 'PUBLISHED');
    """)
    conn.commit()

    # Run migration
    success, msg = run_migration(connection=conn)
    assert success is True
    assert "Successfully added" in msg

    # Verify new columns exist
    cursor.execute("PRAGMA table_info(concepts);")
    cols = {row[1] for row in cursor.fetchall()}
    assert "content" in cols
    assert "tags" in cols
    assert "category" in cols

    # Verify existing data was preserved
    cursor.execute("SELECT title, slug FROM concepts WHERE slug='existing-concept';")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == "Existing Concept"

    # Verify defaults for new columns on existing row
    cursor.execute("SELECT content, tags, category FROM concepts WHERE slug='existing-concept';")
    row = cursor.fetchone()
    assert row[0] is None  # content defaults to NULL
    assert row[1] == "[]"  # tags defaults to empty JSON array
    assert row[2] == ""    # category defaults to empty string

    # Verify idempotency
    success2, msg2 = run_migration(connection=conn)
    assert success2 is True
    assert "already exist" in msg2

    conn.close()
