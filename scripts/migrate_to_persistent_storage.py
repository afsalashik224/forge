#!/usr/bin/env python3
"""
Migrate SQLite database to persistent host storage directory with safety checks.

Requirements:
- Verifies source database existence and SQLite integrity.
- Requires the expected 'concepts' table and validates columns.
- Rejects empty or unrelated SQLite databases.
- Creates timestamped backup prior to migration.
- Never overwrites an existing destination database without explicit verification.
- Preserves source and destination backups.
- Compares record counts and PRAGMA integrity before and after copy.
- Applies least-privilege permissions (0o664 / 0o775, no world-writable permissions).
"""

import datetime
import os
import shutil
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


def verify_and_migrate(source_db, dest_dir):
    print("=== Forge Database Migration to Persistent Storage ===")
    print(f"Source DB:      {source_db}")
    print(f"Target dir:     {dest_dir}")

    if not os.path.exists(source_db):
        raise FileNotFoundError(f"Source database does not exist: {source_db}")

    # Step 1: Verify source DB integrity, schema & count
    src_conn = sqlite3.connect(source_db)
    try:
        src_count = validate_database_schema(src_conn, f"Source DB ({source_db})")
    except Exception:
        src_conn.close()
        raise

    if src_count == 0:
        src_conn.close()
        raise ValueError(f"Source database ({source_db}) contains 0 concepts. Refusing to migrate an empty or unrelated database.")

    print(f"Source DB verified: integrity=ok, concepts_count={src_count}")

    # Step 2: Ensure destination & backup directory
    os.makedirs(dest_dir, exist_ok=True)
    try:
        os.chmod(dest_dir, 0o775)
    except Exception:
        pass

    backup_dir = os.path.join(dest_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    try:
        os.chmod(backup_dir, 0o775)
    except Exception:
        pass

    dest_db = os.path.join(dest_dir, "forge.db")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Step 3: Always create a timestamped backup of the source database first
    backup_file = os.path.join(backup_dir, f"forge_source_backup_{timestamp}.db")
    print(f"Creating timestamped source backup at: {backup_file}")
    backup_conn = sqlite3.connect(backup_file)
    src_conn.backup(backup_conn)
    backup_conn.close()
    src_conn.close()

    # Verify source backup
    chk_conn = sqlite3.connect(backup_file)
    try:
        chk_count = validate_database_schema(chk_conn, f"Backup DB ({backup_file})")
    finally:
        chk_conn.close()

    if chk_count != src_count:
        raise ValueError(f"Backup record count mismatch: {chk_count} != {src_count}")
    try:
        os.chmod(backup_file, 0o664)
    except Exception:
        pass
    print("Source backup verified successfully.")

    # Step 4: If destination already exists, verify it; never blindly overwrite
    if os.path.exists(dest_db):
        print(f"Target DB already exists at {dest_db}. Verifying existing target...")
        dst_conn = sqlite3.connect(dest_db)
        try:
            dst_count = validate_database_schema(dst_conn, f"Target DB ({dest_db})")
        except Exception:
            dst_conn.close()
            raise

        # Preserve existing destination backup before any action
        dest_backup_file = os.path.join(backup_dir, f"forge_existing_dest_backup_{timestamp}.db")
        print(f"Preserving existing destination backup at: {dest_backup_file}")
        dest_bk_conn = sqlite3.connect(dest_backup_file)
        dst_conn.backup(dest_bk_conn)
        dest_bk_conn.close()
        dst_conn.close()
        try:
            os.chmod(dest_backup_file, 0o664)
        except Exception:
            pass

        # Never overwrite an existing verified database if it already contains the data
        if dst_count >= src_count:
            print(f"Target DB already active and verified with {dst_count} concepts (>= source count {src_count}). Keeping existing target database.")
            try:
                os.chmod(dest_db, 0o664)
            except Exception:
                pass
            return dest_db, dst_count
        else:
            raise ValueError(
                f"Destination database already exists at {dest_db} with {dst_count} concepts, "
                f"which is fewer than source ({src_count} concepts). Refusing to overwrite without manual confirmation."
            )

    # Step 5: Copy to destination using sqlite online backup
    print(f"Migrating database to destination: {dest_db}")
    src_conn2 = sqlite3.connect(source_db)
    dst_conn2 = sqlite3.connect(dest_db)
    src_conn2.backup(dst_conn2)
    dst_conn2.close()
    src_conn2.close()

    # Step 6: Verify destination database
    final_conn = sqlite3.connect(dest_db)
    try:
        final_count = validate_database_schema(final_conn, f"Migrated destination DB ({dest_db})")
    finally:
        final_conn.close()

    if final_count != src_count:
        raise ValueError(f"Migration count mismatch: source had {src_count}, target has {final_count}")

    try:
        os.chmod(dest_db, 0o664)
    except Exception:
        pass

    print(f"[MIGRATION SUCCESS] Target database ready at {dest_db} with {final_count} concepts.")
    return dest_db, final_count


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_src = os.path.join(base, "backend", "instance", "forge.db")
    default_dst = os.path.join(base, "data")
    src = sys.argv[1] if len(sys.argv) > 1 else default_src
    dst = sys.argv[2] if len(sys.argv) > 2 else default_dst
    verify_and_migrate(src, dst)
