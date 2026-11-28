# Forge Production Deployment & Schema Upgrade Guide

## Overview

Forge uses a persistent SQLite database mounted into the backend container at `/app/instance/forge.db` from host path `${FORGE_DATA_DIR:-$HOME/forge/data}/forge.db`.

Because `backend/.dockerignore` keeps `migrations/` and `tests/` out of the production Docker image, schema migrations (`001`–`005`) are executed on the **deployment host** by [scripts/run_migrations.py](file:///d:/forge/scripts/run_migrations.py) inside [scripts/deploy.sh](file:///d:/forge/scripts/deploy.sh) prior to building/activating the new container.

---

## Deployment & Upgrade Sequence (`scripts/deploy.sh`)

1. **State Detection**: Inspects host `$DATA_DIR/forge.db`, `$FORGE_LEGACY_DB`, and existing Docker container `forge` (fails closed on ambiguous container vs. legacy DB sources unless `FORGE_MIGRATION_SOURCE` is set).
2. **Database Backup / Extraction**:
   - If `$DATA_DIR/forge.db` already exists: creates and verifies a timestamped backup via `scripts/backup_db.py`.
   - If migrating from an old container or legacy host DB: gracefully stops running containers to flush WAL/SHM writes and runs `scripts/migrate_to_persistent_storage.py`.
3. **Ordered Host-Side Schema Upgrade (`001` → `005`)**:
   - Runs `python3 scripts/run_migrations.py "$DATA_DIR/forge.db" "$BACKUP_DIR"`.
   - Creates a verified `forge_premigration_<timestamp>.db` backup before applying `001_add_updated_at` through `005_add_compass_recommendations` idempotently.
   - Verifies `PRAGMA integrity_check == ok`, presence of all 7 expected tables (`concepts`, `workspaces`, `repositories`, `workspace_repositories`, `repository_concepts`, `concept_relationships`, `compass_recommendations`) and required columns, and preservation of every pre-existing concept `(id, slug)`.
   - Automatically restores the pre-migration backup if any migration step or verification check fails.
4. **Docker Image Build & Fresh Schema Initialization**:
   - Builds `forge-backend` with `migrations/` and `.env*` excluded via `backend/.dockerignore`.
   - On fresh installations (when no `forge.db` existed prior to build), initializes the schema via `db.create_all()`, applies `0664` permissions, and runs `run_migrations.py --verify-only`.
5. **Safe Container Swap & Post-Deploy Verification**:
   - Renames existing `forge` container to `forge-previous` (without deleting it or unrelated containers/volumes).
   - Starts the new `forge` container with `-v "$DATA_DIR:/app/instance"`.
   - Probes `/health` and all Phases 0–5 endpoints (`/api/concepts/`, `/api/workspaces/`, `/api/repositories/`, `/api/graph/`, `/api/progress/`, `/api/compass/`).
   - Removes `forge-previous` only after every check succeeds.

---

## Rollback Behavior

If a failure occurs at **any stage**:
- **Migration Failure (Step 3)**: `run_migrations.py` immediately restores the verified pre-migration backup to `$DATA_DIR/forge.db`; `deploy.sh` aborts without swapping containers and restarts the existing `forge` container if it was temporarily stopped for snapshot copy.
- **Image Build / Container Start / Health or API Verification Failure (Steps 4–5)**: `cleanup_and_rollback()` restores `$DATA_DIR/forge.db` from the pre-migration backup (when an existing DB was upgraded in that run), removes the failed container, renames `forge-previous` back to `forge`, and restores its prior running/stopped state.

---

## File Permissions Policy

- Host data & backup directories (`$DATA_DIR`, `$DATA_DIR/backups`): `0775` (allows WAL/SHM creation without world write).
- SQLite database & backup files (`forge.db`, backups): `0664` (owner & group read/write, never world-writable `0666`).
