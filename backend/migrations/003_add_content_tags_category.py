"""
Migration 003: Add content, tags, and category columns to concepts table.

Safe and idempotent:
- Adds 'content' TEXT column if not exists.
- Adds 'tags' TEXT column (JSON-serialized list) if not exists.
- Adds 'category' VARCHAR(50) column if not exists.
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

        # Check existing columns
        cursor.execute("PRAGMA table_info(concepts);")
        existing_cols = {row[1] for row in cursor.fetchall()}

        added = []

        if "content" not in existing_cols:
            cursor.execute("ALTER TABLE concepts ADD COLUMN content TEXT;")
            added.append("content")

        if "tags" not in existing_cols:
            cursor.execute("ALTER TABLE concepts ADD COLUMN tags TEXT DEFAULT '[]';")
            added.append("tags")

        if "category" not in existing_cols:
            cursor.execute("ALTER TABLE concepts ADD COLUMN category VARCHAR(50) DEFAULT '';")
            added.append("category")

        connection.commit()

        if added:
            return True, f"Successfully added columns: {', '.join(added)}."
        else:
            return True, "All columns (content, tags, category) already exist — skipped."

    except Exception as exc:
        if connection:
            connection.rollback()
        return False, f"Migration 003 failed: {str(exc)}"

    finally:
        if close_conn and connection:
            connection.close()


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else None
    success, msg = run_migration(db_path=db_file)
    print(f"[{'SUCCESS' if success else 'FAILURE'}] {msg}")
    sys.exit(0 if success else 1)
