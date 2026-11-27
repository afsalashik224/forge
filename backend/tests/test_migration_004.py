import sqlite3
from migrations import run_migration_004 as run_migration


def test_migration_004_creates_concept_relationships_table():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

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
    cursor.execute(
        "INSERT INTO concepts (title, slug) VALUES ('Concept A', 'concept-a'), ('Concept B', 'concept-b');"
    )
    conn.commit()

    success, msg = run_migration(connection=conn)
    assert success is True
    assert "concept_relationships" in msg

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    assert "concept_relationships" in tables

    # Verify check constraint rejects self-loops
    failed_self_loop = False
    try:
        cursor.execute(
            "INSERT INTO concept_relationships (source_concept_id, target_concept_id, relationship_type) VALUES (1, 1, 'RELATES_TO');"
        )
    except sqlite3.IntegrityError:
        failed_self_loop = True
    assert failed_self_loop is True

    # Verify valid insert works and unique constraint rejects duplicate edge
    cursor.execute(
        "INSERT INTO concept_relationships (source_concept_id, target_concept_id, relationship_type, description) "
        "VALUES (1, 2, 'DEPENDS_ON', 'A needs B');"
    )
    conn.commit()

    failed_duplicate = False
    try:
        cursor.execute(
            "INSERT INTO concept_relationships (source_concept_id, target_concept_id, relationship_type) "
            "VALUES (1, 2, 'DEPENDS_ON');"
        )
    except sqlite3.IntegrityError:
        failed_duplicate = True
    assert failed_duplicate is True

    # Idempotency check
    success2, _ = run_migration(connection=conn)
    assert success2 is True

    conn.close()
