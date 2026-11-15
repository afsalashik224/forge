#!/usr/bin/env python3
"""
Database Backup & Verification Tool for Forge.

Features:
- Verifies source database existence and SQLite integrity.
- Uses sqlite3 online backup API for safe, non-destructive copying.
- Creates timestamped backups in the designated backup directory.
- Verifies backup integrity and row count against the source.
- Never overwrites without explicit confirmation.
"""

import datetime
import os
import sqlite3
import sys

def backup_database(source_path=None, backup_dir=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if source_path is None:
        source_path = os.path.join(base_dir, "backend", "instance", "forge.db")
    
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source database not found at: {source_path}")

    # Step 1: Verify source database integrity
    src_conn = sqlite3.connect(source_path)
    src_cur = src_conn.cursor()
    try:
        src_cur.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    except Exception:
        pass
    src_cur.execute("PRAGMA integrity_check;")
    src_integrity = src_cur.fetchone()[0]
    if src_integrity != "ok":
        src_conn.close()
        raise ValueError(f"Source database failed integrity check: {src_integrity}")

    src_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='concepts';")
    if src_cur.fetchone():
        src_cur.execute("SELECT COUNT(*) FROM concepts;")
        source_count = src_cur.fetchone()[0]
    else:
        source_count = 0

    # Step 2: Determine backup path
    if backup_dir is None:
        backup_dir = os.path.join(base_dir, "backend", "instance", "backups")
    os.makedirs(backup_dir, exist_ok=True)

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
    chk_cur = chk_conn.cursor()
    chk_cur.execute("PRAGMA integrity_check;")
    backup_integrity = chk_cur.fetchone()[0]
    if backup_integrity != "ok":
        chk_conn.close()
        raise ValueError(f"Backup database failed integrity check: {backup_integrity}")

    chk_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='concepts';")
    if chk_cur.fetchone():
        chk_cur.execute("SELECT COUNT(*) FROM concepts;")
        backup_count = chk_cur.fetchone()[0]
    else:
        backup_count = 0
    chk_conn.close()

    if source_count != backup_count:
        raise ValueError(f"Record count mismatch: source had {source_count}, backup has {backup_count}")

    print(f"[BACKUP SUCCESS]")
    print(f"  Source:      {source_path}")
    print(f"  Destination: {backup_path}")
    print(f"  Integrity:   {backup_integrity}")
    print(f"  Records:     {backup_count} concepts verified")
    return backup_path, backup_count


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else None
    dest = sys.argv[2] if len(sys.argv) > 2 else None
    backup_database(src, dest)
