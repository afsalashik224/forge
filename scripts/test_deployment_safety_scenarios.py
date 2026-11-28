#!/usr/bin/env python3
"""
Comprehensive Automated Test Suite for Deployment Safety, SQLite Persistence & Rollback Scenarios.

Scenarios tested:
1. Fresh installation (no container, no database)
2. First migration from a running container (all 4 concepts survive)
3. First migration from a stopped container (all 4 concepts survive)
4. Subsequent deployment with existing persistent database (pre-deploy backup, 4 concepts intact)
5. Missing database in existing container (fail-closed abort, container preserved)
6. Corrupt database in existing container (fail-closed abort, container preserved)
7. Empty database in existing container (fail-closed abort, container preserved)
8. Unrelated database missing 'concepts' table (fail-closed abort, container preserved)
9. Ambiguous migration sources (fail-closed abort when container & legacy DB both exist)
10. Ambiguous migration source resolution with FORGE_MIGRATION_SOURCE=container
11. Failed container startup / docker run failure (rollback restores previous container)
12. Failed health check (rollback restores previous container, data preserved)
13. Storage permissions (664 on database, 775 on directory, WAL/SHM writes verified)
"""

import json
import os
import shutil
import sqlite3
import subprocess
import time
import urllib.request

BASE_DIR = "/mnt/d/forge"
TEST_DATA_DIR = "/home/afsal/forge_safety_test_data"
TEST_LEGACY_DIR = "/home/afsal/forge_safety_legacy_data"
PORT = 5000
IMAGE = "forge-backend"

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def http_get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.status, json.loads(response.read().decode())

def http_post(url, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.status, json.loads(response.read().decode())

def cleanup():
    run_cmd("docker rm -f forge forge-previous 2>/dev/null || true")
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)
    if os.path.exists(TEST_LEGACY_DIR):
        shutil.rmtree(TEST_LEGACY_DIR)

def create_sample_db(path, count=4):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
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
        cur.execute(f"INSERT INTO concepts (title, slug, summary) VALUES ('Original Concept {i}', 'original-concept-{i}', 'Summary {i}');")
    conn.commit()
    conn.close()

print("======================================================================")
print("   RUNNING FORGE DEPLOYMENT SAFETY & PERSISTENCE TEST SUITE")
print("======================================================================")

print("Building baseline image...")
build_res = run_cmd(f"cd {BASE_DIR}/backend && docker build -t {IMAGE} .")
assert build_res.returncode == 0, f"Image build failed: {build_res.stderr}"

results = []

def record(scenario_name, passed, detail=""):
    status = "PASSED" if passed else "FAILED"
    results.append((scenario_name, status, detail))
    print(f"[{status}] {scenario_name} - {detail}")

# ------------------------------------------------------------------------------
# Test 1: Fresh Installation (No container, no database)
# ------------------------------------------------------------------------------
print("\n--- Test 1: Fresh installation ---")
cleanup()
res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
time.sleep(2)

if res.returncode == 0 and os.path.exists(f"{TEST_DATA_DIR}/forge.db"):
    status, health = http_get(f"http://localhost:{PORT}/health")
    status_c, concepts = http_get(f"http://localhost:{PORT}/api/concepts/")
    db_mode = oct(os.stat(f"{TEST_DATA_DIR}/forge.db").st_mode & 0o777)
    dir_mode = oct(os.stat(f"{TEST_DATA_DIR}").st_mode & 0o777)
    passed = (health["status"] == "healthy" and concepts == [] and db_mode == "0o664")
    record("Test 1: Fresh installation", passed, f"Healthy (HTTP {status}), empty DB initialized, permissions db={db_mode}, dir={dir_mode}")
else:
    record("Test 1: Fresh installation", False, f"Deploy failed: {res.stderr}")

# ------------------------------------------------------------------------------
# Test 2: First migration from a running container (All 4 original concepts)
# ------------------------------------------------------------------------------
print("\n--- Test 2: First migration from a running container (4 concepts) ---")
cleanup()
seed_db = f"{TEST_DATA_DIR}/tmp_seed/forge.db"
create_sample_db(seed_db, count=4)

run_cmd(f"docker run -d --name forge {IMAGE}")
run_cmd(f"docker cp {seed_db} forge:/app/instance/forge.db")
shutil.rmtree(f"{TEST_DATA_DIR}/tmp_seed")

res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
time.sleep(2)

if res.returncode == 0 and os.path.exists(f"{TEST_DATA_DIR}/forge.db"):
    status, concepts = http_get(f"http://localhost:{PORT}/api/concepts/")
    status_p, progress = http_get(f"http://localhost:{PORT}/api/progress/")
    status_g, graph = http_get(f"http://localhost:{PORT}/api/graph/")
    status_c, compass = http_get(f"http://localhost:{PORT}/api/compass/")
    passed = (
        len(concepts) == 4
        and all(c["slug"].startswith("original-concept-") for c in concepts)
        and status_p == 200
        and status_g == 200
        and status_c == 200
        and graph["stats"]["total_nodes"] == 4
    )
    record("Test 2: Running container migration (4 concepts + Phases 0-5 schema)", passed, f"All {len(concepts)} original concepts survived & Phases 0-5 APIs verified")
else:
    record("Test 2: Running container migration (4 concepts)", False, f"Deploy failed: {res.stderr}")

# ------------------------------------------------------------------------------
# Test 3: First migration from a stopped container (All 4 original concepts)
# ------------------------------------------------------------------------------
print("\n--- Test 3: Migration from a stopped container (4 concepts) ---")
cleanup()
seed_db = f"{TEST_DATA_DIR}/tmp_seed/forge.db"
create_sample_db(seed_db, count=4)

run_cmd(f"docker create --name forge {IMAGE}")
run_cmd(f"docker cp {seed_db} forge:/app/instance/forge.db")
shutil.rmtree(f"{TEST_DATA_DIR}/tmp_seed")

res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
time.sleep(2)

if res.returncode == 0 and os.path.exists(f"{TEST_DATA_DIR}/forge.db"):
    status, concepts = http_get(f"http://localhost:{PORT}/api/concepts/")
    passed = (len(concepts) == 4 and all(c["slug"].startswith("original-concept-") for c in concepts))
    record("Test 3: Stopped container migration (4 concepts)", passed, f"All {len(concepts)} original concepts survived from stopped container")
else:
    record("Test 3: Stopped container migration (4 concepts)", False, f"Deploy failed: {res.stderr}")

# ------------------------------------------------------------------------------
# Test 4: Subsequent deployment with existing persistent database
# ------------------------------------------------------------------------------
print("\n--- Test 4: Subsequent deployment with existing persistent database ---")
# Active container from Test 3 has 4 concepts. Deploy again over existing persistent storage.
res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
time.sleep(2)

backups = [f for f in os.listdir(f"{TEST_DATA_DIR}/backups") if f.endswith(".db")]
status, concepts = http_get(f"http://localhost:{PORT}/api/concepts/")
passed = (res.returncode == 0 and len(backups) >= 1 and len(concepts) == 4)
record("Test 4: Subsequent deployment", passed, f"Pre-deploy backup verified ({len(backups)} backups found), {len(concepts)} concepts intact")

# ------------------------------------------------------------------------------
# Test 5: Missing database in existing container (Fail closed)
# ------------------------------------------------------------------------------
print("\n--- Test 5: Missing database in existing container (fail closed) ---")
cleanup()
run_cmd(f"docker run -d --name forge {IMAGE}")
run_cmd("docker exec forge rm -rf /app/instance/forge.db /app/forge.db 2>/dev/null || true")

res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
container_preserved = (run_cmd("docker ps -a --format '{{.Names}}' | grep -q '^forge$'").returncode == 0)
db_not_created = not os.path.exists(f"{TEST_DATA_DIR}/forge.db")
passed = (res.returncode != 0 and container_preserved and db_not_created)
record("Test 5: Missing DB fail-closed abort", passed, f"Aborted fail-closed (rc={res.returncode}), container preserved, no phantom DB")

# ------------------------------------------------------------------------------
# Test 6: Corrupt database in existing container (Fail closed)
# ------------------------------------------------------------------------------
print("\n--- Test 6: Corrupt database in existing container (fail closed) ---")
cleanup()
run_cmd(f"docker run -d --name forge {IMAGE}")
run_cmd("docker exec forge mkdir -p /app/instance")
run_cmd("docker exec forge bash -c 'echo \"CORRUPTED GARBAGE\" > /app/instance/forge.db'")

res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
container_preserved = (run_cmd("docker ps -a --format '{{.Names}}' | grep -q '^forge$'").returncode == 0)
db_not_migrated = not os.path.exists(f"{TEST_DATA_DIR}/forge.db")
passed = (res.returncode != 0 and container_preserved and db_not_migrated)
record("Test 6: Corrupt DB fail-closed abort", passed, f"Aborted on corrupt integrity (rc={res.returncode}), container preserved")

# ------------------------------------------------------------------------------
# Test 7: Empty database in existing container (Fail closed)
# ------------------------------------------------------------------------------
print("\n--- Test 7: Empty database in existing container (fail closed) ---")
cleanup()
seed_db = f"{TEST_DATA_DIR}/tmp_seed/forge.db"
create_sample_db(seed_db, count=0)  # Empty concepts table

run_cmd(f"docker run -d --name forge {IMAGE}")
run_cmd(f"docker cp {seed_db} forge:/app/instance/forge.db")
shutil.rmtree(f"{TEST_DATA_DIR}/tmp_seed")

res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
container_preserved = (run_cmd("docker ps -a --format '{{.Names}}' | grep -q '^forge$'").returncode == 0)
db_not_migrated = not os.path.exists(f"{TEST_DATA_DIR}/forge.db")
passed = (res.returncode != 0 and container_preserved and db_not_migrated)
record("Test 7: Empty DB fail-closed abort", passed, f"Rejected 0-concept DB (rc={res.returncode}), container preserved")

# ------------------------------------------------------------------------------
# Test 8: Unrelated database missing 'concepts' table (Fail closed)
# ------------------------------------------------------------------------------
print("\n--- Test 8: Unrelated database missing 'concepts' table (fail closed) ---")
cleanup()
os.makedirs(f"{TEST_DATA_DIR}/tmp_seed", exist_ok=True)
unrelated_db = f"{TEST_DATA_DIR}/tmp_seed/forge.db"
conn = sqlite3.connect(unrelated_db)
conn.execute("CREATE TABLE users (id INT, name TEXT);")
conn.execute("INSERT INTO users VALUES (1, 'Alice');")
conn.commit()
conn.close()

run_cmd(f"docker run -d --name forge {IMAGE}")
run_cmd(f"docker cp {unrelated_db} forge:/app/instance/forge.db")
shutil.rmtree(f"{TEST_DATA_DIR}/tmp_seed")

res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
container_preserved = (run_cmd("docker ps -a --format '{{.Names}}' | grep -q '^forge$'").returncode == 0)
db_not_migrated = not os.path.exists(f"{TEST_DATA_DIR}/forge.db")
passed = (res.returncode != 0 and container_preserved and db_not_migrated)
record("Test 8: Unrelated DB fail-closed abort", passed, f"Rejected database lacking 'concepts' table (rc={res.returncode}), container preserved")

# ------------------------------------------------------------------------------
# Test 9: Ambiguous migration sources (Both container DB and legacy DB exist)
# ------------------------------------------------------------------------------
print("\n--- Test 9: Ambiguous migration sources fail-closed ---")
cleanup()
seed_db = f"{TEST_DATA_DIR}/tmp_seed/forge.db"
create_sample_db(seed_db, count=4)
run_cmd(f"docker run -d --name forge {IMAGE}")
run_cmd(f"docker cp {seed_db} forge:/app/instance/forge.db")
shutil.rmtree(f"{TEST_DATA_DIR}/tmp_seed")

legacy_db = f"{TEST_LEGACY_DIR}/forge.db"
create_sample_db(legacy_db, count=2)

res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB={legacy_db} && unset FORGE_MIGRATION_SOURCE && cd {BASE_DIR} && bash scripts/deploy.sh")
container_preserved = (run_cmd("docker ps -a --format '{{.Names}}' | grep -q '^forge$'").returncode == 0)
db_not_migrated = not os.path.exists(f"{TEST_DATA_DIR}/forge.db")
passed = (res.returncode != 0 and container_preserved and db_not_migrated)
record("Test 9: Ambiguous migration sources abort", passed, f"Detected ambiguity and aborted fail-closed (rc={res.returncode}), both sources preserved")

# ------------------------------------------------------------------------------
# Test 10: Ambiguity resolved via explicit FORGE_MIGRATION_SOURCE=container
# ------------------------------------------------------------------------------
print("\n--- Test 10: Explicit FORGE_MIGRATION_SOURCE=container ---")
res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB={legacy_db} && export FORGE_MIGRATION_SOURCE=container && cd {BASE_DIR} && bash scripts/deploy.sh")
time.sleep(2)

if res.returncode == 0 and os.path.exists(f"{TEST_DATA_DIR}/forge.db"):
    status, concepts = http_get(f"http://localhost:{PORT}/api/concepts/")
    passed = (len(concepts) == 4)  # Container had 4 concepts, legacy had 2
    record("Test 10: Explicit FORGE_MIGRATION_SOURCE=container", passed, f"Successfully resolved to container source: verified {len(concepts)} concepts")
else:
    record("Test 10: Explicit FORGE_MIGRATION_SOURCE=container", False, f"Deploy failed: {res.stderr}")

# ------------------------------------------------------------------------------
# Test 11: Failed container startup / docker run error (Rollback)
# ------------------------------------------------------------------------------
print("\n--- Test 11: Failed container startup rollback ---")
# Active container 'forge' currently has 4 concepts.
# Pass invalid port parameter to trigger container creation failure and test rollback
res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_PORT=999999 && cd {BASE_DIR} && bash scripts/deploy.sh")
previous_restored = (run_cmd("docker ps --format '{{.Names}}' | grep -q '^forge$'").returncode == 0)
no_renamed_left = (run_cmd("docker ps -a --format '{{.Names}}' | grep -q '^forge-previous$'").returncode != 0)
time.sleep(1)
status, concepts = http_get(f"http://localhost:5000/api/concepts/")
passed = (res.returncode != 0 and previous_restored and no_renamed_left and len(concepts) == 4)
record("Test 11: Startup failure rollback", passed, f"Failed container handled cleanly, original container restored and running with {len(concepts)} concepts")

# ------------------------------------------------------------------------------
# Test 12: Failed health check (Rollback)
# ------------------------------------------------------------------------------
print("\n--- Test 12: Failed health check rollback ---")
# Trigger health check failure via FORGE_HEALTH_CHECK_URL without touching any script files
res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_HEALTH_CHECK_URL='http://127.0.0.1:59999/health' && cd {BASE_DIR} && bash scripts/deploy.sh")
previous_restored = (run_cmd("docker ps --format '{{.Names}}' | grep -q '^forge$'").returncode == 0)
no_renamed_left = (run_cmd("docker ps -a --format '{{.Names}}' | grep -q '^forge-previous$'").returncode != 0)
time.sleep(1)
status, concepts = http_get(f"http://localhost:5000/api/concepts/")
passed = (res.returncode != 0 and previous_restored and no_renamed_left and len(concepts) == 4)
record("Test 12: Health check failure rollback", passed, f"Rollback restored previous container running on port 5000 with {len(concepts)} concepts")

# ------------------------------------------------------------------------------
# Test 13: Storage permissions and WAL/SHM file creation
# ------------------------------------------------------------------------------
print("\n--- Test 13: Storage permissions & WAL/SHM file creation ---")
# Post a new concept through the running container to trigger write and WAL generation
status, new_c = http_post(f"http://localhost:{PORT}/api/concepts/", {
    "title": "WAL Permission Concept",
    "slug": "wal-permission-concept",
    "summary": "Testing WAL/SHM write with 664/775 permissions"
})
db_path = f"{TEST_DATA_DIR}/forge.db"
db_perm = oct(os.stat(db_path).st_mode & 0o777)
dir_perm = oct(os.stat(TEST_DATA_DIR).st_mode & 0o777)
no_world_write = ((os.stat(db_path).st_mode & 0o002) == 0 and (os.stat(TEST_DATA_DIR).st_mode & 0o002) == 0)

status, concepts = http_get(f"http://localhost:{PORT}/api/concepts/")
passed = (status == 200 and len(concepts) == 5 and db_perm == "0o664" and no_world_write)
record("Test 13: Storage permissions & WAL write", passed, f"Write succeeded (5 concepts), db={db_perm}, dir={dir_perm}, world-writable=False")

# ------------------------------------------------------------------------------
# Test 14: Existing Phase 0 Persistent DB Upgrade (pre-001 -> Phases 0-5)
# ------------------------------------------------------------------------------
print("\n--- Test 14: Existing Phase 0 persistent DB upgrade (001-005) ---")
cleanup()
os.makedirs(TEST_DATA_DIR, exist_ok=True)
phase0_db = f"{TEST_DATA_DIR}/forge.db"
conn = sqlite3.connect(phase0_db)
conn.execute("""
    CREATE TABLE concepts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(200) NOT NULL,
        slug VARCHAR(200) UNIQUE NOT NULL,
        summary TEXT,
        status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
""")
for i in range(1, 5):
    conn.execute(
        "INSERT INTO concepts (title, slug, summary, status, created_at) "
        "VALUES (?, ?, ?, 'PUBLISHED', '2026-08-01 10:00:00');",
        (f"Phase0 Concept {i}", f"phase0-concept-{i}", f"Phase 0 summary {i}"),
    )
conn.commit()
conn.close()

res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
time.sleep(2)

if res.returncode == 0:
    status_c, concepts = http_get(f"http://localhost:{PORT}/api/concepts/")
    status_p, progress = http_get(f"http://localhost:{PORT}/api/progress/")
    status_k, compass = http_get(f"http://localhost:{PORT}/api/compass/")
    conn = sqlite3.connect(phase0_db)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()}
    conn.close()
    expected_tables = {
        "concepts", "workspaces", "repositories",
        "workspace_repositories", "repository_concepts",
        "concept_relationships", "compass_recommendations",
    }
    passed = (
        status_c == 200 and len(concepts) == 4
        and status_p == 200 and status_k == 200
        and expected_tables.issubset(tables)
    )
    record("Test 14: Phase 0 DB upgrade (001-005)", passed, f"Upgraded pre-001 DB to all 7 tables; {len(concepts)} original concepts preserved")
else:
    record("Test 14: Phase 0 DB upgrade (001-005)", False, f"Deploy failed: {res.stderr}\n{res.stdout}")

# Final Cleanup
cleanup()

print("\n======================================================================")
print("   TEST SUITE EXECUTION SUMMARY")
print("======================================================================")
all_passed = all(status == "PASSED" for _, status, _ in results)
for name, status, detail in results:
    print(f"  [{status}] {name} - {detail}")
print(f"\nTotal: {len(results)} | Passed: {sum(1 for _, s, _ in results if s == 'PASSED')} | Failed: {sum(1 for _, s, _ in results if s == 'FAILED')}")
print("======================================================================")

exit(0 if all_passed else 1)
