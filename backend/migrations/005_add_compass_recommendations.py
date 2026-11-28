"""
Migration 005: Add compass_recommendations table for Forge Compass.

Safe and idempotent:
- Creates 'compass_recommendations' table if not exists.
- Creates indexes on dedupe_key, status, priority, and entity reference.
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
            CREATE TABLE IF NOT EXISTS compass_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dedupe_key VARCHAR(200) UNIQUE NOT NULL,
                rule_code VARCHAR(64) NOT NULL,
                title VARCHAR(200) NOT NULL,
                explanation TEXT NOT NULL,
                category VARCHAR(50) NOT NULL,
                priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
                entity_type VARCHAR(30),
                entity_id INTEGER,
                entity_slug VARCHAR(200),
                entity_label VARCHAR(200),
                evidence_json TEXT NOT NULL DEFAULT '{}',
                suggested_action TEXT NOT NULL,
                action_target VARCHAR(50) NOT NULL DEFAULT 'library',
                status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                resolved_at DATETIME,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_compass_dedupe_key ON compass_recommendations(dedupe_key);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_compass_status ON compass_recommendations(status);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_compass_priority ON compass_recommendations(priority);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS ix_compass_entity ON compass_recommendations(entity_type, entity_id);"
        )

        connection.commit()
        return True, "Successfully created compass_recommendations table and indexes."

    except Exception as exc:
        if connection:
            connection.rollback()
        return False, f"Migration 005 failed: {str(exc)}"

    finally:
        if close_conn and connection:
            connection.close()


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else None
    success, msg = run_migration(db_path=db_file)
    print(f"[{'SUCCESS' if success else 'FAILURE'}] {msg}")
    sys.exit(0 if success else 1)
