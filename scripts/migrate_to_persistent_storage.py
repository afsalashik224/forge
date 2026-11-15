#!/usr/bin/env python3
"""
Migrate SQLite database to persistent host storage directory with safety checks.

Requirements:
- Verifies source database existence and SQLite integrity.
- Creates timestamped backup prior to migration.
- Never overwrites an existing destination database without verification.
- Compares record counts and PRAGMA integrity before and after copy.
"""

import datetime
import os
import shutil
import sqlite3
import sys

def verify_and_migrate(source_db, dest_dir):
    print("=== Forge Database Migration to Persistent Storage ===")
    print(f"Source DB:      {source_db}")
    print(f"Target dir:     {dest_dir}")

    if not os.path.exists(source_db):
        raise FileNotFoundError(f"Source database does not exist: {source_db}")

    # Step 1: Verify source DB integrity & count
    src_conn = sqlite3.connect(source_db)
    src_cur = src_conn.cursor()
    try:
        src_cur.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    except Exception:
        pass
    src_cur.execute("PRAGMA integrity_check;")
    src_check = src_cur.fetchone()[0]
    if src_check != "ok":
        src_conn.close()
        raise ValueError(f"Source database integrity check failed: {src_check}")

    src_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='concepts';")
    if src_cur.fetchone():
        src_cur.execute("SELECT COUNT(*) FROM concepts;")
        src_count = src_cur.fetchone()[0]
    else:
        src_count = 0
    print(f"Source DB verified: integrity=ok, concepts_count={src_count}")

    # Step 2: Ensure destination & backup directory
    os.makedirs(dest_dir, exist_ok=True)
    backup_dir = os.path.join(dest_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    dest_db = os.path.join(dest_dir, "forge.db")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Step 3: Always create a timestamped backup first
    backup_file = os.path.join(backup_dir, f"forge_pre_deploy_{timestamp}.db")
    print(f"Creating timestamped backup at: {backup_file}")
    backup_conn = sqlite3.connect(backup_file)
    src_conn.backup(backup_conn)
    backup_conn.close()
    src_conn.close()

    # Verify backup
    chk_conn = sqlite3.connect(backup_file)
    chk_cur = chk_conn.cursor()
    chk_cur.execute("PRAGMA integrity_check;")
    assert chk_cur.fetchone()[0] == "ok", "Backup failed integrity check"
    chk_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='concepts';")
    if chk_cur.fetchone():
        chk_cur.execute("SELECT COUNT(*) FROM concepts;")
        chk_count = chk_cur.fetchone()[0]
    else:
        chk_count = 0
    assert chk_count == src_count, f"Backup record count mismatch: {chk_count} != {src_count}"
    chk_conn.close()
    print("Backup verified successfully.")

    # Step 4: If destination already exists, verify it; do not blindly overwrite
    if os.path.exists(dest_db):
        print(f"Target DB already exists at {dest_db}. Verifying existing target...")
        dst_conn = sqlite3.connect(dest_db)
        dst_cur = dst_conn.cursor()
        dst_cur.execute("PRAGMA integrity_check;")
        dst_check = dst_cur.fetchone()[0]
        if dst_check != "ok":
            dst_conn.close()
            raise ValueError(f"Existing target DB failed integrity check: {dst_check}")
        dst_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='concepts';")
        if dst_cur.fetchone():
            dst_cur.execute("SELECT COUNT(*) FROM concepts;")
            dst_count = dst_cur.fetchone()[0]
        else:
            dst_count = 0
        dst_conn.close()
        print(f"Target DB already active: integrity=ok, concepts_count={dst_count}")
        return dest_db, dst_count

    # Step 5: Copy to destination using sqlite online backup
    print(f"Migrating database to destination: {dest_db}")
    src_conn2 = sqlite3.connect(source_db)
    dst_conn2 = sqlite3.connect(dest_db)
    src_conn2.backup(dst_conn2)
    dst_conn2.close()
    src_conn2.close()

    # Step 6: Verify destination database
    final_conn = sqlite3.connect(dest_db)
    final_cur = final_conn.cursor()
    final_cur.execute("PRAGMA integrity_check;")
    final_check = final_cur.fetchone()[0]
    if final_check != "ok":
        final_conn.close()
        raise ValueError(f"Migrated destination DB failed integrity check: {final_check}")

    final_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='concepts';")
    if final_cur.fetchone():
        final_cur.execute("SELECT COUNT(*) FROM concepts;")
        final_count = final_cur.fetchone()[0]
    else:
        final_count = 0
    final_conn.close()

    if final_count != src_count:
        raise ValueError(f"Migration count mismatch: source had {src_count}, target has {final_count}")

    print(f"[MIGRATION SUCCESS] Target database ready at {dest_db} with {final_count} concepts.")
    return dest_db, final_count


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_src = os.path.join(base, "backend", "instance", "forge.db")
    default_dst = os.path.join(base, "data")
    src = sys.argv[1] if len(sys.argv) > 1 else default_src
    dst = sys.argv[2] if len(sys.argv) > 2 else default_dst
    verify_and_migrate(src, dst)
