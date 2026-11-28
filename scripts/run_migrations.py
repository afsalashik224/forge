#!/usr/bin/env python3
"""
Ordered Schema Migration Runner & Verifier for Forge (Migrations 001-005).

Runs on the deployment host (outside the Docker build context) using Python's
standard library so backend/migrations/ can remain excluded via .dockerignore.

Safety guarantees:
1. Validates SQLite integrity and base 'concepts' table before touching anything.
2. Creates and verifies a timestamped pre-migration backup via sqlite3.backup().
3. Runs migrations 001 -> 005 in deterministic order (all idempotent).
4. Verifies complete Phase 0-5 schema (all 7 tables + required columns), SQLite
   integrity, and preservation of all pre-existing concept records.
5. Restores the pre-migration backup automatically if any step or check fails.
6. Enforces least-privilege 0o664 / 0o775 permissions (never world-writable).
"""

import argparse
import datetime
import importlib
import os
import sqlite3
import sys


FORGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(FORGE_ROOT, "backend")

BASE_REQUIRED_CONCEPT_COLUMNS = {"id", "title", "slug", "summary", "status", "created_at"}

MIGRATION_STEPS = [
    ("001", "migrations.001_add_updated_at"),
    ("002", "migrations.002_add_workspaces_and_repositories"),
    ("003", "migrations.003_add_content_tags_category"),
    ("004", "migrations.004_add_concept_relationships"),
    ("005", "migrations.005_add_compass_recommendations"),
]

EXPECTED_SCHEMA = {
    "concepts": {
        "id", "title", "slug", "summary", "status", "created_at",
        "updated_at", "content", "tags", "category",
    },
    "workspaces": {
        "id", "name", "slug", "description", "created_at", "updated_at",
    },
    "repositories": {
        "id", "name", "slug", "description", "vcs_url",
        "primary_language", "status", "created_at", "updated_at",
    },
    "workspace_repositories": {
        "workspace_id", "repository_id", "created_at",
    },
    "repository_concepts": {
        "repository_id", "concept_id", "created_at",
    },
    "concept_relationships": {
        "id", "source_concept_id", "target_concept_id",
        "relationship_type", "description", "created_at", "updated_at",
    },
    "compass_recommendations": {
        "id", "dedupe_key", "rule_code", "title", "explanation",
        "category", "priority", "entity_type", "entity_id",
        "entity_slug", "entity_label", "evidence_json", "suggested_action",
        "action_target", "status", "is_active", "resolved_at",
        "created_at", "updated_at",
    },
}


def _ensure_backend_on_path():
    if BACKEND_DIR not in sys.path:
        sys.path.insert(0, BACKEND_DIR)


def _sqlite_backup(src_path, dst_path):
    """Copy a SQLite database safely using the online backup API."""
    src_conn = sqlite3.connect(src_path)
    dst_conn = sqlite3.connect(dst_path)
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()


def validate_base_database(db_path):
    """Verify SQLite integrity and base 'concepts' table prior to migration."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file does not exist: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        try:
            cur.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        except Exception:
            pass

        cur.execute("PRAGMA integrity_check;")
        check = cur.fetchone()[0]
        if check != "ok":
            raise ValueError(f"Database '{db_path}' failed SQLite integrity_check: {check}")

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='concepts';")
        if not cur.fetchone():
            raise ValueError(f"Database '{db_path}' is missing required table 'concepts'.")

        cur.execute("PRAGMA table_info(concepts);")
        cols = {row[1] for row in cur.fetchall()}
        missing = BASE_REQUIRED_CONCEPT_COLUMNS - cols
        if missing:
            raise ValueError(f"Table 'concepts' is missing required base columns: {sorted(missing)}")

        cur.execute("SELECT id, slug FROM concepts;")
        rows = cur.fetchall()
        return len(rows), set(rows)
    finally:
        conn.close()


def verify_complete_schema(db_path, expected_min_count=0, expected_concept_pairs=None):
    """Verify SQLite integrity, complete Phases 0-5 schema, and preserved concept records."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        check = cur.fetchone()[0]
        if check != "ok":
            raise ValueError(f"Post-migration integrity check failed: {check}")

        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = {row[0] for row in cur.fetchall()}

        missing_tables = set(EXPECTED_SCHEMA.keys()) - existing_tables
        if missing_tables:
            raise ValueError(f"Schema missing required table(s): {sorted(missing_tables)}")

        for table, expected_cols in EXPECTED_SCHEMA.items():
            cur.execute(f"PRAGMA table_info({table});")
            actual_cols = {row[1] for row in cur.fetchall()}
            missing_cols = expected_cols - actual_cols
            if missing_cols:
                raise ValueError(
                    f"Table '{table}' is missing required column(s): {sorted(missing_cols)}"
                )

        cur.execute("SELECT id, slug FROM concepts;")
        current_rows = cur.fetchall()
        current_pairs = set(current_rows)
        if len(current_rows) < expected_min_count:
            raise ValueError(
                f"Concept record count dropped after migration: {len(current_rows)} < {expected_min_count}"
            )
        if expected_concept_pairs and not expected_concept_pairs.issubset(current_pairs):
            lost = expected_concept_pairs - current_pairs
            raise ValueError(f"Existing concept record(s) missing after migration: {lost}")

        return len(current_rows)
    finally:
        conn.close()


def restore_database_backup(backup_path, db_path):
    """Restore pre-migration backup back to db_path cleanly."""
    if not backup_path or not os.path.exists(backup_path):
        raise FileNotFoundError(f"Cannot restore missing backup: {backup_path}")

    for suffix in ("-wal", "-shm"):
        sidecar = f"{db_path}{suffix}"
        if os.path.exists(sidecar):
            try:
                os.remove(sidecar)
            except OSError:
                pass

    _sqlite_backup(backup_path, db_path)
    try:
        os.chmod(db_path, 0o664)
    except OSError:
        pass


def upgrade_database(
    db_path,
    backup_dir=None,
    restore_on_failure=True,
    inject_failure_step=None,
    verify_only=False,
):
    """
    Create a verified backup, run migrations 001-005 in order, and verify completeness.
    Restores the pre-migration backup if any migration or post-check fails.
    """
    _ensure_backend_on_path()

    pre_count, pre_pairs = validate_base_database(db_path)

    if backup_dir is None:
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(db_path)), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    try:
        os.chmod(backup_dir, 0o775)
    except OSError:
        pass

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_path = os.path.join(backup_dir, f"forge_premigration_{timestamp}.db")
    _sqlite_backup(db_path, backup_path)
    try:
        os.chmod(backup_path, 0o664)
    except OSError:
        pass

    # Verify backup integrity & record count before mutating source
    bk_count, _ = validate_base_database(backup_path)
    if bk_count != pre_count:
        raise ValueError(f"Pre-migration backup count mismatch: {bk_count} != {pre_count}")

    step_results = []
    conn = None
    try:
        if not verify_only:
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA foreign_keys = ON;")
            for step_id, module_name in MIGRATION_STEPS:
                if inject_failure_step == step_id:
                    raise RuntimeError(f"Injected failure during migration step {step_id}.")
                mod = importlib.import_module(module_name)
                success, msg = mod.run_migration(connection=conn)
                if not success:
                    raise RuntimeError(f"Migration {step_id} ({module_name}) failed: {msg}")
                step_results.append((step_id, msg))
            conn.close()
            conn = None

        post_count = verify_complete_schema(
            db_path,
            expected_min_count=pre_count,
            expected_concept_pairs=pre_pairs,
        )

        try:
            os.chmod(db_path, 0o664)
        except OSError:
            pass

        return {
            "db_path": db_path,
            "backup_path": backup_path,
            "pre_count": pre_count,
            "post_count": post_count,
            "steps": step_results,
            "tables_verified": sorted(EXPECTED_SCHEMA.keys()),
        }

    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
            conn.close()
        if restore_on_failure:
            restore_database_backup(backup_path, db_path)
        raise


def main():
    parser = argparse.ArgumentParser(description="Run Forge SQLite migrations 001-005 safely.")
    parser.add_argument("db_path", help="Path to SQLite database file (e.g. ~/forge/data/forge.db)")
    parser.add_argument("backup_dir", nargs="?", default=None, help="Directory for pre-migration backup")
    parser.add_argument("--verify-only", action="store_true", help="Only verify schema completeness without altering DB")
    parser.add_argument("--backup-path-file", default=None, help="Optional file path to write the pre-migration backup path")
    args = parser.parse_args()

    print("=== Forge Host Migration Runner (001-005) ===")
    print(f"Target DB: {args.db_path}")

    try:
        result = upgrade_database(
            db_path=args.db_path,
            backup_dir=args.backup_dir,
            restore_on_failure=True,
            verify_only=args.verify_only,
        )
    except Exception as exc:
        print(f"[MIGRATION FAILURE] {exc}", file=sys.stderr)
        sys.exit(1)

    if args.backup_path_file:
        with open(args.backup_path_file, "w", encoding="utf-8") as fh:
            fh.write(result["backup_path"])

    print(f"Pre-migration backup: {result['backup_path']}")
    for step_id, msg in result["steps"]:
        print(f"  [{step_id}] {msg}")
    print(
        f"[MIGRATION SUCCESS] Verified {len(result['tables_verified'])} tables and "
        f"{result['post_count']} preserved concept(s)."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
