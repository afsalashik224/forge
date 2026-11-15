# Forge — Phase 0: Stability Hardening & Backend Reliability

**Branch:** `feature/forge-foundation`  
**Base Commit:** `c3a6155` (`docs(readme): enhance project documentation for v1.0`)  
**Status:** Completed & Verified — Awaiting Approval for Phase 1  
**Date:** 2026-11-15  

---

## 1. Executive Summary

Phase 0 focused on hardening the existing Forge foundation without altering product architecture or introducing out-of-scope features. Prior to Phase 0, the backend suffered from unhandled exceptions on `POST /api/concepts/` (returning 500 on bad input or duplicate slugs), flawed timestamp semantics (`created_at` overwritten on update), secrets baked into Docker images, unseparated test dependencies, absent automated testing in CI, a broken mobile sidebar, and a critical persistence flaw where container removal (`docker rm forge`) wiped the SQLite database.

All identified vulnerabilities, data integrity issues, persistence mechanisms, and test gaps have been addressed, verified against an isolated test environment, and confirmed through a live Docker multi-container persistence demonstration with zero data loss.

---

## 2. Inventory of Changes

### 2.1 Backend Core & Data Layer

#### 1. Timestamp Correction
- **File:** `backend/app/models/concept.py`
- **Issue:** `created_at` used `onupdate=db.func.now()`, causing it to act as an update timestamp and overwrite the original creation time on any record edit.
- **Solution:** 
  - `created_at` is now immutable: `server_default=db.func.now(), nullable=False` (no `onupdate`).
  - Added `updated_at`: `server_default=db.func.now(), onupdate=db.func.now(), nullable=True`.
  - When records are inserted, both are set to current timestamp. On updates, only `updated_at` changes.

#### 2. Safe & Idempotent Migration
- **Files:** `backend/migrations/001_add_updated_at.py`, `backend/migrations/__init__.py`
- **Mechanism:**
  - Inspects SQLite catalog via `PRAGMA table_info(concepts);`.
  - If `updated_at` does not exist, runs `ALTER TABLE concepts ADD COLUMN updated_at DATETIME;`.
  - Backfills existing records: `UPDATE concepts SET updated_at = created_at WHERE updated_at IS NULL;`.
  - If `updated_at` is already present, skips execution safely with no errors.
  - Can be executed via CLI (`python -m migrations.001_add_updated_at`) or imported programmatically.

#### 3. API Input Validation & Error Handling
- **File:** `backend/app/api/concept_api.py`
- **Enhancements:**
  - **Content-Type Validation:** Rejects non-JSON requests with `400 Bad Request`.
  - **Payload Validation:** Ensures request body is a valid JSON object.
  - **Field Checks:** Requires `title` and `slug`; rejects missing, null, non-string, or blank whitespace-only values with `400 Bad Request`.
  - **Duplicate Prevention:** Catches `ValueError` from service layer and returns `409 Conflict` with clear error details.
  - **Unexpected Errors:** Catches unanticipated exceptions and returns `500 Internal Server Error` without leaking stack traces.
  - **Timestamp Serialization:** Exposes ISO-formatted `created_at` and `updated_at` on all concept responses (`POST /api/concepts/`, `GET /api/concepts/`, `GET /api/concepts/<slug>`).
  - **Backwards Compatibility:** Response bodies include both `"error"` and `"message"` keys so existing frontend toast handlers (`data.message`) continue functioning without breaking.

#### 4. Global Application Error Handlers
- **File:** `backend/app/__init__.py`
- **Enhancements:**
  - Added `test_config` parameter to `create_app(test_config=None)` to support in-memory test databases and isolated test runners.
  - Added registered handlers for `400`, `404`, `405`, and `500` returning standardized JSON error payloads.

---

### 2.2 Persistent SQLite Storage & Docker Hardening

#### 1. Container Database Path & Explicit Absolute URI
- **Exact Container Path:** `/app/instance/forge.db`
- **Explicit SQLite URI:** `DATABASE_URL=sqlite:////app/instance/forge.db` (4 slashes -> absolute path).
- **Dockerfile Update (`backend/Dockerfile`):**
  - Declared `ENV DATABASE_URL=sqlite:////app/instance/forge.db`.
  - Declared `VOLUME ["/app/instance"]`.
  - Switched CMD to production Gunicorn: `CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app.app:app"]`.

#### 2. Host Storage Mount & Safety Guard in Deployment
- **File:** `scripts/deploy.sh`
- **Host Data Directory:** `DATA_DIR="${FORGE_DATA_DIR:-$HOME/forge/data}"`
- **Persistence Mechanism:** 
  - Directory is ensured before container runs: `mkdir -p "$DATA_DIR/backups"` with `chmod 755 "$DATA_DIR"`.
  - Pre-deployment check verifies if a database exists; if so, it creates a timestamped backup before touching containers.
  - Container runs with bind mount: `-v "$DATA_DIR:/app/instance"`.
  - When `docker rm forge` runs during future deployments, `$DATA_DIR/forge.db` on the host is **never removed**, and the newly created container immediately mounts the existing database.

#### 3. Database Migration & Timestamped Backup Scripts
- **`scripts/backup_db.py`:** Uses SQLite's online backup API (`sqlite3.backup()`) to perform safe, consistent database backups with pre- and post-copy integrity checks and record count verification.
- **`scripts/migrate_to_persistent_storage.py`:** Safely migrates an existing instance database to persistent host storage without data loss, verifying schema and concept records before and after transfer.

---

### 2.3 Automated Testing & CI/CD Pipeline

#### 1. Pytest Test Suites (21 Tests Passing)
- **`backend/tests/conftest.py`:** Pytest fixtures configuring `TESTING=True`, an in-memory SQLite database (`sqlite:///:memory:`), test client, and automatic table creation/cleanup per test.
- **`backend/tests/test_service.py`:** Unit tests verifying concept creation, duplicate slug rejection, retrieval, and empty states.
- **`backend/tests/test_repository.py`:** Unit tests verifying database operations, queries, and timestamp immutability.
- **`backend/tests/test_api.py`:** Integration tests verifying HTTP status codes across all routes: `/health` (200), `POST` (201, 400, 409), `GET` (200, 404), and JSON serialization.
- **`backend/tests/test_migration.py`:** Unit tests verifying schema migration from old table structure to new, data preservation, backfill accuracy, and idempotency.

#### 2. GitHub Actions CI Gating
- **File:** `.github/workflows/backend.yml`
- **Updates:**
  - Installs `requirements-dev.txt`.
  - Runs `pytest tests/ -v` (21 tests).
  - Verifies app initialization: `python -c "from app import create_app; app = create_app(); print('App initialized successfully')"`.
  - Builds Docker image using production `requirements.txt`.
  - Gated EC2 deployment: only runs if CI tests pass AND only on pushes to `main` (`if: github.ref == 'refs/heads/main' && github.event_name == 'push'`). Feature branches run CI checks but do not deploy.

---

### 2.4 Frontend Mobile Navigation Fix

- **`frontend/src/App.jsx`:** Introduced `isMobileOpen` state. Passed `isMobileOpen` and `onCloseMobile={() => setIsMobileOpen(false)}` to `<Sidebar>`, and `onOpenMobileSidebar={() => setIsMobileOpen(true)}` to `<Header>`.
- **`frontend/src/components/Header.jsx`:** Added hamburger toggle button (`<Menu size={16} />`) next to breadcrumbs.
- **`frontend/src/index.css`:** Added `.mobile-menu-btn` (hidden on desktop, visible on `<= 768px`) and hidden `.desktop-sidebar-container` on `<= 768px`. Desktop visual layout remains 100% untouched.

---

## 3. Verification & Demonstration Results

### 3.1 Deployment Safety & Persistent Migration Test Suite (8/8 Scenarios Passing)
Executed `scripts/test_deployment_safety_scenarios.py` in the WSL Docker environment:

```text
======================================================================
   RUNNING DEPLOYMENT SAFETY & PERSISTENCE TEST SUITE
======================================================================
Building baseline image...

--- Test 1: First migration from a running container ---
[PASSED] Scenario 1: Running container migration - Extracted & verified 4 concepts

--- Test 2: Migration from a stopped container ---
[PASSED] Scenario 2: Stopped container migration - Extracted from stopped container: 3 concepts

--- Test 3: Subsequent deployment with existing persistent database ---
[PASSED] Scenario 3: Subsequent deployment - Pre-deploy backup created (2 in backup dir), concepts preserved: 4

--- Test 4: Missing database in existing container (fail-closed) ---
[PASSED] Scenario 4: Missing DB fail-closed abort - Aborted cleanly (rc=1), container preserved, no phantom DB created

--- Test 5: Corrupt database integrity failure (fail-closed) ---
[PASSED] Scenario 5: Corrupt DB integrity fail-closed - Aborted cleanly on corrupt check (rc=1), container preserved

--- Test 6: Interrupted migration safety ---
[PASSED] Scenario 6: Interrupted migration safety - Verified pre-deploy backup exists and active database is uncorrupted

--- Test 7: Fresh installation ---
[PASSED] Scenario 7: Fresh installation - Fresh container healthy (HTTP 200), mounted empty DB (0 concepts)

--- Test 8: Container recreation with existing persistent data ---
[PASSED] Scenario 8: Container recreation with existing data - Data survived container deletion (found 1 concept: 'persistent-concept')

======================================================================
   TEST SUITE EXECUTION SUMMARY
======================================================================
  [PASSED] Scenario 1: Running container migration - Extracted & verified 4 concepts
  [PASSED] Scenario 2: Stopped container migration - Extracted from stopped container: 3 concepts
  [PASSED] Scenario 3: Subsequent deployment - Pre-deploy backup created (2 in backup dir), concepts preserved: 4
  [PASSED] Scenario 4: Missing DB fail-closed abort - Aborted cleanly (rc=1), container preserved, no phantom DB created
  [PASSED] Scenario 5: Corrupt DB integrity fail-closed - Aborted cleanly on corrupt check (rc=1), container preserved
  [PASSED] Scenario 6: Interrupted migration safety - Verified pre-deploy backup exists and active database is uncorrupted
  [PASSED] Scenario 7: Fresh installation - Fresh container healthy (HTTP 200), mounted empty DB (0 concepts)
  [PASSED] Scenario 8: Container recreation with existing data - Data survived container deletion (found 1 concept: 'persistent-concept')

Total: 8 | Passed: 8 | Failed: 0
======================================================================
```

### 3.2 Docker Persistence Demonstration Across Container Deletion
Executed `scripts/test_docker_persistence.py` in the WSL Docker environment:

```text
=== Starting Docker Persistence Demonstration ===
=== Forge Database Migration to Persistent Storage ===
Source DB:      /mnt/d/forge/backend/instance/forge.db
Target dir:     /home/afsal/forge_docker_test_data
Source DB verified: integrity=ok, concepts_count=4
Creating timestamped backup at: /home/afsal/forge_docker_test_data/backups/forge_pre_deploy_20261115_120305.db
Backup verified successfully.
Migrating database to destination: /home/afsal/forge_docker_test_data/forge.db
[MIGRATION SUCCESS] Target database ready at /home/afsal/forge_docker_test_data/forge.db with 4 concepts.

[Step 1] Starting Container 1 ('forge-test-1') mounting /home/afsal/forge_docker_test_data to /app/instance...
  Container 1 Health: HTTP 200 -> healthy
  Container 1 Initial Concepts Count: 4
    - [1] Git Branches (git-branches)
    - [2] REST API (rest-api)
    - [3] Docker (docker)
    - [4] Docker (docker-basic commands)

[Step 2] Adding 5th concept to Container 1 via POST /api/concepts/...
  Created concept: HTTP 201 -> ID #5 (Persistent Container Storage)
  Container 1 Concept Count after creation: 5

[Step 3] DESTROYING Container 1 ('docker stop' and 'docker rm')...
  Verifying Container 1 is deleted: '' (empty means fully removed)

[Step 4] Starting brand new Container 2 ('forge-test-2') with the same volume mount...
  Container 2 Health: HTTP 200 -> healthy

[Step 5] Querying concepts from Container 2...
  Container 2 Concepts Count: 5
    - [1] Git Branches (git-branches)
    - [2] REST API (rest-api)
    - [3] Docker (docker)
    - [4] Docker (docker-basic commands)
    - [5] Persistent Container Storage (persistent-container-storage)

=== PERSISTENCE DEMONSTRATION PASSED ===
All 5 concepts (including original 4 and newly inserted 5th) survived container deletion and recreation!
```

### 3.3 Pytest Suite (21 Tests Passing)
```text
$ pytest -v
============================= test session starts ==============================
platform linux -- Python 3.14.4, pytest-8.3.5, pluggy-1.7.0 -- /mnt/d/forge/backend/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /mnt/d/forge/backend
plugins: flask-1.3.0
collecting ... collected 21 items

tests/test_api.py::test_health_endpoint PASSED                           [  4%]
tests/test_api.py::test_get_concepts_empty_initially PASSED              [  9%]
tests/test_api.py::test_create_concept_success_201 PASSED                [ 14%]
tests/test_api.py::test_create_concept_non_json_returns_400 PASSED       [ 19%]
tests/test_api.py::test_create_concept_missing_title_returns_400 PASSED  [ 23%]
tests/test_api.py::test_create_concept_empty_title_returns_400 PASSED    [ 28%]
tests/test_api.py::test_create_concept_missing_slug_returns_400 PASSED   [ 33%]
tests/test_api.py::test_create_concept_invalid_type_returns_400 PASSED   [ 38%]
tests/test_api.py::test_create_concept_duplicate_slug_returns_409 PASSED [ 42%]
tests/test_api.py::test_get_concept_by_slug_found_and_not_found PASSED   [ 47%]
tests/test_api.py::test_get_all_concepts_returns_list PASSED             [ 52%]
tests/test_migration.py::test_migration_adds_column_and_preserves_data PASSED [ 57%]
tests/test_repository.py::test_repository_create_and_get_by_id PASSED    [ 61%]
tests/test_repository.py::test_repository_get_by_slug PASSED             [ 66%]
tests/test_repository.py::test_repository_get_all PASSED                 [ 71%]
tests/test_repository.py::test_concept_timestamp_semantics PASSED        [ 76%]
tests/test_service.py::test_create_concept_success PASSED                [ 80%]
tests/test_service.py::test_create_concept_duplicate_slug_rejected PASSED [ 85%]
tests/test_service.py::test_get_concept_by_slug_existing PASSED          [ 90%]
tests/test_service.py::test_get_concept_by_slug_nonexistent PASSED       [ 95%]
tests/test_service.py::test_get_all_concepts_empty_and_populated PASSED  [100%]

============================== 21 passed in 0.49s ==============================
```

### 3.4 Live Database Migration & Data Audit (`backend/instance/forge.db`)
- **Integrity Check:** `ok`
- **Active Concepts in Host DB:** 4 concepts verified:
  - `[1] Git Branches` (`git-branches`): `created_at: 2026-08-03 09:50:06` \| `updated_at: 2026-08-03 09:50:06`
  - `[2] REST API` (`rest-api`): `created_at: 2026-08-03 13:31:22` \| `updated_at: 2026-08-03 13:31:22`
  - `[3] Docker` (`docker`): `created_at: 2026-08-03 16:07:54` \| `updated_at: 2026-08-03 16:07:54`
  - `[4] Docker` (`docker-basic commands`): `created_at: 2026-08-05 15:50:44` \| `updated_at: 2026-08-05 15:50:44`
- **Backup Created & Verified:** `backend/instance/backups/forge_backup_20261115_120455.db` (Integrity: `ok`, 4 records).

---

## 4. Git Working Tree State

```text
On branch feature/forge-foundation
Changes not staged for commit:
	modified:   .github/workflows/backend.yml
	modified:   .gitignore
	modified:   backend/.dockerignore
	modified:   backend/.env.example
	modified:   backend/Dockerfile
	modified:   backend/app/__init__.py
	modified:   backend/app/api/concept_api.py
	modified:   backend/app/models/concept.py
	modified:   backend/requirements.txt
	modified:   backend/tests/test_repository.py
	modified:   backend/tests/test_service.py
	modified:   frontend/src/App.jsx
	modified:   frontend/src/components/Header.jsx
	modified:   frontend/src/index.css
	modified:   scripts/deploy.sh

Untracked files:
	backend/migrations/
	backend/requirements-dev.txt
	backend/tests/conftest.py
	backend/tests/test_api.py
	backend/tests/test_migration.py
	backend/tests/verify_phase0.py
	docs/PHASE_0_SUMMARY.md
	scripts/backup_db.py
	scripts/migrate_to_persistent_storage.py
	scripts/test_deployment_safety_scenarios.py
	scripts/test_docker_persistence.py
```

no changes added to commit (use "git add" and/or "git commit -a")
```

---

## 5. Next Phase Readiness

Phase 0 is complete. Persistent storage, timestamp semantics, API error handling, and test coverage have been fully validated. The branch `feature/forge-foundation` is ready for **Phase 1: Concept Lifecycle Management (CRUD - Edit & Delete)**.
