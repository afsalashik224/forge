"""
Migration 004: Add concept_relationships table for the Knowledge Graph.

Safe and idempotent:
- Creates 'concept_relationships' table if not exists.
- Creates indexes on source_concept_id, target_concept_id, and unique constraint index.
"""

import os
import sqlite3
import sys


def get_db_path():
    """Resolve the SQLite database path from environment or default locations."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///forge.db")

    if database_url.startswith("sqlite:///"):
        path = database_url[len("sqlite:///"):]
    else:
        path = database_url

    if not os.path.isabs(path):
        instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", path)
        if os.path.exists(instance_path):
            return instance_path
        cwd_instance = os.path.join(os.getcwd(), "instance", path)
        if os.path.exists(cwd_instance):
            return cwd_instance
        cwd_path = os.path.join(os.getcwd(), path)
        if os.path.exists(cwd_path):
            return cwd_path
        return instance_path

    return path


def run_migration(connection=None, db_path=None):
    """
    Run migration on the provided sqlite3 connection or resolve from db_path.
    Returns (success: bool, message: str)
    """
    close_conn = False
    if connection is None:
        if db_path is None:
            db_path = get_db_path()
        if not os.path.exists(db_path):
            return False, f"Database file not found at: {db_path}"
        connection = sqlite3.connect(db_path)
        close_conn = True

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concept_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
                target_concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
                relationship_type VARCHAR(40) NOT NULL,
                description TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CHECK (source_concept_id != target_concept_id),
                UNIQUE (source_concept_id, target_concept_id, relationship_type)
            );
        """)

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_concept_rel_source ON concept_relationships(source_concept_id);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_concept_rel_target ON concept_relationships(target_concept_id);"
        )
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_concept_rel_edge "
            "ON concept_relationships(source_concept_id, target_concept_id, relationship_type);"
        )

        connection.commit()
        return True, "Successfully created concept_relationships table and indexes."

    except Exception as exc:
        if connection:
            connection.rollback()
        return False, f"Migration 004 failed: {str(exc)}"

    finally:
        if close_conn and connection:
            connection.close()


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else None
    success, msg = run_migration(db_path=db_file)
    print(f"[{'SUCCESS' if success else 'FAILURE'}] {msg}")
    sys.exit(0 if success else 1)
