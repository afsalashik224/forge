"""
Migration 001: Add updated_at column to concepts table.

Safe and idempotent:
- Checks if 'concepts' table exists.
- Checks if 'updated_at' column already exists in 'concepts'.
- If missing, executes: ALTER TABLE concepts ADD COLUMN updated_at DATETIME;
- Populates existing rows: UPDATE concepts SET updated_at = created_at WHERE updated_at IS NULL;
- If column already exists, performs no action.
"""

import os
import sqlite3
import sys

def get_db_path():
    """Resolve the SQLite database path from environment or default locations."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///forge.db")
    
    # Strip sqlite:/// prefix
    if database_url.startswith("sqlite:///"):
        path = database_url[len("sqlite:///"):]
    else:
        path = database_url

    # If it's a relative path, check instance/forge.db or current dir
    if not os.path.isabs(path):
        instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", path)
        if os.path.exists(instance_path):
            return instance_path
        # Also check current working directory
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
        
        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='concepts';")
        if not cursor.fetchone():
            return False, "Table 'concepts' does not exist. Run init_db first."

        # Check existing columns
        cursor.execute("PRAGMA table_info(concepts);")
        columns = [row[1] for row in cursor.fetchall()]

        if "updated_at" in columns:
            return True, "Column 'updated_at' already exists on 'concepts'. Migration skipped (idempotent)."

        # Add column
        cursor.execute("ALTER TABLE concepts ADD COLUMN updated_at DATETIME;")
        
        # Backfill existing rows with created_at value
        cursor.execute("UPDATE concepts SET updated_at = created_at WHERE updated_at IS NULL;")
        
        connection.commit()
        return True, "Successfully added 'updated_at' column and backfilled existing records."

    except Exception as exc:
        if connection:
            connection.rollback()
        return False, f"Migration failed: {str(exc)}"

    finally:
        if close_conn and connection:
            connection.close()


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else None
    success, msg = run_migration(db_path=db_file)
    print(f"[{'SUCCESS' if success else 'FAILURE'}] {msg}")
    sys.exit(0 if success else 1)
