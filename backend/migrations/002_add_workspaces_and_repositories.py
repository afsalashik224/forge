"""
Migration 002: Add workspaces, repositories, and association tables.

Safe and idempotent:
- Creates 'workspaces' table if not exists.
- Creates 'repositories' table if not exists.
- Creates 'workspace_repositories' association table if not exists.
- Creates 'repository_concepts' association table if not exists.
- Creates unique indexes if not exists.
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

        # 1. Create workspaces table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                slug VARCHAR(120) UNIQUE NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_workspaces_slug ON workspaces(slug);")

        # 2. Create repositories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(120) NOT NULL,
                slug VARCHAR(140) UNIQUE NOT NULL,
                description TEXT,
                vcs_url VARCHAR(300),
                primary_language VARCHAR(50),
                status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_repositories_slug ON repositories(slug);")

        # 3. Create workspace_repositories association table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspace_repositories (
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (workspace_id, repository_id)
            );
        """)

        # 4. Create repository_concepts association table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repository_concepts (
                repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
                concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (repository_id, concept_id)
            );
        """)

        connection.commit()
        return True, "Successfully created workspaces, repositories, and association tables."

    except Exception as exc:
        if connection:
            connection.rollback()
        return False, f"Migration 002 failed: {str(exc)}"

    finally:
        if close_conn and connection:
            connection.close()


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else None
    success, msg = run_migration(db_path=db_file)
    print(f"[{'SUCCESS' if success else 'FAILURE'}] {msg}")
    sys.exit(0 if success else 1)
