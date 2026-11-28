import sqlite3
from migrations import run_migration_005 as run_migration


def test_migration_005_creates_compass_table_and_indexes():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    success, msg = run_migration(connection=conn)
    assert success is True
    assert "compass_recommendations" in msg

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    assert "compass_recommendations" in tables

    cursor.execute("PRAGMA table_info(compass_recommendations);")
    cols = {row[1] for row in cursor.fetchall()}
    for expected in (
        "id",
        "dedupe_key",
        "rule_code",
        "title",
        "explanation",
        "category",
        "priority",
        "entity_type",
        "entity_id",
        "evidence_json",
        "suggested_action",
        "status",
        "is_active",
        "resolved_at",
    ):
        assert expected in cols

    # Verify idempotency
    success2, _ = run_migration(connection=conn)
    assert success2 is True
    conn.close()
