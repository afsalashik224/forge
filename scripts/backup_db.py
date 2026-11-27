#!/usr/bin/env python3
"""
Database Backup & Verification Tool for Forge.

Features:
- Verifies source database existence, SQLite integrity, and schema.
- Requires the expected 'concepts' table and validates columns.
- Uses sqlite3 online backup API for safe, non-destructive copying.
- Creates timestamped backups in the designated backup directory.
- Verifies backup integrity and row count against the source.
- Uses least-privilege 0o664 file permissions (no world-writable permissions).
- Never overwrites without explicit confirmation.
"""

import datetime
import os
import sqlite3
import sys

REQUIRED_COLUMNS = {"id", "title", "slug", "summary", "status", "created_at"}


def validate_database_schema(conn, db_path="Database"):
    """Validates that the database has integrity and the expected concepts table & columns."""
    cur = conn.cursor()

    try:
        cur.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    except Exception:
        pass

    cur.execute("PRAGMA integrity_check;")
    check = cur.fetchone()[0]
    if check != "ok":
        raise ValueError(f"{db_path} failed SQLite integrity check: {check}")

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='concepts';")
    if not cur.fetchone():
        raise ValueError(f"{db_path} is missing required table 'concepts'. Not a valid Forge database.")

    cur.execute("PRAGMA table_info(concepts);")
    columns = {row[1] for row in cur.fetchall()}
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise ValueError(f"{db_path} 'concepts' table is missing required columns: {missing}")

    cur.execute("SELECT COUNT(*) FROM concepts;")
    count = cur.fetchone()[0]
    return count


def backup_database(source_path=None, backup_dir=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if source_path is None:
        source_path = os.path.join(base_dir, "backend", "instance", "forge.db")

    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source database not found at: {source_path}")

    # Step 1: Verify source database integrity and schema
    src_conn = sqlite3.connect(source_path)
    try:
        source_count = validate_database_schema(src_conn, f"Source DB ({source_path})")
    except Exception:
        src_conn.close()
        raise

    # Step 2: Determine backup path
    if backup_dir is None:
        backup_dir = os.path.join(base_dir, "backend", "instance", "backups")
    os.makedirs(backup_dir, exist_ok=True)
    try:
        os.chmod(backup_dir, 0o775)
    except Exception:
        pass

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"forge_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)

    if os.path.exists(backup_path):
        src_conn.close()
        raise FileExistsError(f"Backup destination already exists: {backup_path}")

    # Step 3: Perform safe online SQLite backup
    dest_conn = sqlite3.connect(backup_path)
    src_conn.backup(dest_conn)
    dest_conn.close()
    src_conn.close()

    # Step 4: Verify backup database integrity & counts
    chk_conn = sqlite3.connect(backup_path)
    try:
        backup_count = validate_database_schema(chk_conn, f"Backup DB ({backup_path})")
    finally:
        chk_conn.close()

    if source_count != backup_count:
        raise ValueError(f"Record count mismatch: source had {source_count}, backup has {backup_count}")

    try:
        os.chmod(backup_path, 0o664)
    except Exception:
        pass

    print("[BACKUP SUCCESS]")
    print(f"  Source:      {source_path}")
    print(f"  Destination: {backup_path}")
    print(f"  Integrity:   ok")
    print(f"  Records:     {backup_count} concepts verified")
    return backup_path, backup_count


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else None
    dest = sys.argv[2] if len(sys.argv) > 2 else None
    backup_database(src, dest)
