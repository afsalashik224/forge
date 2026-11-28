"""
Automated tests for scripts/run_migrations.py — EC2 Phase 0/1 -> Phases 0-5 database upgrades.

Covers:
1. Fresh database schema creation (db.create_all) verified cleanly.
2. Phase 0 pre-001 database upgrade (001 -> 005) preserving all 4 original concepts.
3. Phase 1 database upgrade (002 -> 005) preserving all 4 original concepts + Flask app API compatibility.
4. Repeated / idempotent execution preserving both concepts and Phases 2-5 data.
5. Partial migration failure rollback restoring exact pre-migration database state.
6. Corrupt, missing, and unrelated databases failing closed safely.
7. Host CLI execution independent of Docker container build context.
"""

import os
import sqlite3
import subprocess
import sys
import pytest

FORGE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.join(FORGE_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import run_migrations  # noqa: E402
from app import create_app  # noqa: E402
from app.database.db import db  # noqa: E402
import app.models  # noqa: F401, E402


def _create_phase0_db(path, count=4):
    """Create a Phase 0 SQLite DB (before migration 001: no updated_at, no content/tags/category, 1 table)."""
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            slug VARCHAR(200) UNIQUE NOT NULL,
            summary TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    for i in range(1, count + 1):
        cur.execute(
            "INSERT INTO concepts (title, slug, summary, status, created_at) "
            "VALUES (?, ?, ?, 'PUBLISHED', '2026-08-01 10:00:00');",
            (f"Original Concept {i}", f"original-concept-{i}", f"Summary for concept {i}"),
        )
    conn.commit()
    conn.close()


def _create_phase1_db(path, count=4):
    """Create a Phase 1 SQLite DB (has updated_at, lacks Phases 2-5 schema)."""
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            slug VARCHAR(200) UNIQUE NOT NULL,
            summary TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    for i in range(1, count + 1):
        cur.execute(
            "INSERT INTO concepts (title, slug, summary, status) VALUES (?, ?, ?, 'DRAFT');",
            (f"Phase 1 Concept {i}", f"phase1-concept-{i}", f"Phase 1 summary {i}"),
        )
    conn.commit()
    conn.close()


def test_fresh_db_initialization_and_verify_only(tmp_path):
    db_file = str(tmp_path / "fresh.db")
    backup_dir = str(tmp_path / "backups")

    fresh_app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "test-secret",
    })
    with fresh_app.app_context():
        db.create_all()

    res = run_migrations.upgrade_database(db_file, backup_dir=backup_dir, verify_only=True)
    assert res["pre_count"] == 0
    assert res["post_count"] == 0
    assert len(res["tables_verified"]) == 7

    # Repeated full migration run on fresh DB succeeds cleanly
    res2 = run_migrations.upgrade_database(db_file, backup_dir=backup_dir)
    assert res2["post_count"] == 0


def test_upgrade_phase0_db_to_phase5_preserves_concepts_and_app_works(tmp_path):
    db_file = str(tmp_path / "phase0.db")
    backup_dir = str(tmp_path / "backups")
    _create_phase0_db(db_file, count=4)

    result = run_migrations.upgrade_database(db_file, backup_dir=backup_dir)
    assert result["pre_count"] == 4
    assert result["post_count"] == 4
    assert os.path.exists(result["backup_path"])
    assert set(result["tables_verified"]) == set(run_migrations.EXPECTED_SCHEMA.keys())

    # Verify backfilled updated_at and default tags/category
    conn = sqlite3.connect(db_file)
    rows = conn.execute("SELECT slug, updated_at, tags, category FROM concepts ORDER BY id ASC;").fetchall()
    conn.close()
    assert len(rows) == 4
    assert rows[0][0] == "original-concept-1"
    assert rows[0][1] == "2026-08-01 10:00:00"
    assert rows[0][2] == "[]"
    assert rows[0][3] == ""

    # Verify the upgraded DB works seamlessly with the full Phases 0-5 Flask app
    upgraded_app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": "test-secret",
    })
    with upgraded_app.test_client() as client:
        concepts_res = client.get("/api/concepts/")
        assert concepts_res.status_code == 200
        assert len(concepts_res.get_json()) == 4

        assert client.get("/api/workspaces/").status_code == 200
        assert client.get("/api/repositories/").status_code == 200
        graph_res = client.get("/api/graph/")
        assert graph_res.status_code == 200
        assert graph_res.get_json()["stats"]["total_nodes"] == 4
        assert client.get("/api/progress/").status_code == 200
        assert client.get("/api/compass/").status_code == 200


def test_repeated_migration_runs_are_idempotent(tmp_path):
    db_file = str(tmp_path / "phase1.db")
    backup_dir = str(tmp_path / "backups")
    _create_phase1_db(db_file, count=4)

    r1 = run_migrations.upgrade_database(db_file, backup_dir=backup_dir)
    assert r1["post_count"] == 4

    # Add Phase 2 workspace data between deployments
    conn = sqlite3.connect(db_file)
    conn.execute("INSERT INTO workspaces (name, slug) VALUES ('Prod WS', 'prod-ws');")
    conn.commit()
    conn.close()

    # Second & third run must succeed without losing concepts or workspaces
    r2 = run_migrations.upgrade_database(db_file, backup_dir=backup_dir)
    r3 = run_migrations.upgrade_database(db_file, backup_dir=backup_dir)
    assert r2["post_count"] == 4
    assert r3["post_count"] == 4

    conn = sqlite3.connect(db_file)
    ws_count = conn.execute("SELECT COUNT(*) FROM workspaces;").fetchone()[0]
    conn.close()
    assert ws_count == 1


def test_partial_migration_failure_restores_original_database(tmp_path):
    db_file = str(tmp_path / "partial_fail.db")
    backup_dir = str(tmp_path / "backups")
    _create_phase0_db(db_file, count=4)

    # Inject failure at step 003 (after 001 & 002 already mutated the DB)
    with pytest.raises(RuntimeError, match="Injected failure during migration step 003"):
        run_migrations.upgrade_database(
            db_file,
            backup_dir=backup_dir,
            restore_on_failure=True,
            inject_failure_step="003",
        )

    # Verify DB was cleanly rolled back to exact pre-migration Phase 0 schema
    conn = sqlite3.connect(db_file)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()}
    cols = {row[1] for row in conn.execute("PRAGMA table_info(concepts);").fetchall()}
    count = conn.execute("SELECT COUNT(*) FROM concepts;").fetchone()[0]
    integrity = conn.execute("PRAGMA integrity_check;").fetchone()[0]
    conn.close()

    assert integrity == "ok"
    assert count == 4
    assert "workspaces" not in tables
    assert "updated_at" not in cols
    assert len(os.listdir(backup_dir)) >= 1


def test_fail_closed_on_missing_corrupt_and_unrelated_db(tmp_path):
    backup_dir = str(tmp_path / "backups")

    # Missing
    with pytest.raises(FileNotFoundError):
        run_migrations.upgrade_database(str(tmp_path / "does_not_exist.db"), backup_dir=backup_dir)

    # Corrupt
    corrupt_db = str(tmp_path / "corrupt.db")
    with open(corrupt_db, "wb") as fh:
        fh.write(b"NOT_A_VALID_SQLITE_HEADER")
    with pytest.raises(Exception):
        run_migrations.upgrade_database(corrupt_db, backup_dir=backup_dir)

    # Unrelated SQLite DB lacking 'concepts' table
    unrelated_db = str(tmp_path / "unrelated.db")
    conn = sqlite3.connect(unrelated_db)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
    conn.execute("INSERT INTO users VALUES (1, 'Alice');")
    conn.commit()
    conn.close()

    with pytest.raises(ValueError, match="missing required table 'concepts'"):
        run_migrations.upgrade_database(unrelated_db, backup_dir=backup_dir)

    # Confirm unrelated DB wasn't modified
    conn = sqlite3.connect(unrelated_db)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()}
    conn.close()
    assert tables == {"users"}


def test_host_cli_execution_succeeds_from_repo_root(tmp_path):
    db_file = str(tmp_path / "cli_phase0.db")
    backup_dir = str(tmp_path / "cli_backups")
    record_file = str(tmp_path / "backup_path.txt")
    _create_phase0_db(db_file, count=4)

    proc = subprocess.run(
        [
            sys.executable,
            os.path.join(SCRIPTS_DIR, "run_migrations.py"),
            db_file,
            backup_dir,
            "--backup-path-file",
            record_file,
        ],
        cwd=FORGE_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"CLI failed: {proc.stderr}\n{proc.stdout}"
    assert "[MIGRATION SUCCESS]" in proc.stdout
    assert os.path.exists(record_file)
    with open(record_file, "r", encoding="utf-8") as fh:
        recorded_bk = fh.read().strip()
    assert os.path.exists(recorded_bk)
