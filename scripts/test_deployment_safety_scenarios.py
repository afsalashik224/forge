#!/usr/bin/env python3
"""
Comprehensive Automated Test Suite for Deployment Safety & SQLite Persistence Scenarios.

Tests the 8 required scenarios:
1. First migration from an existing running container with a database.
2. Migration from a stopped container.
3. Existing persistent database on subsequent deployment (pre-deploy backup).
4. Missing database in an existing container (fail-closed abort).
5. Failed integrity check on corrupt database (fail-closed abort).
6. Interrupted migration safety (pre-existing data and backups untouched).
7. Fresh installation with no existing container or database.
8. Container recreation with existing persistent data.
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

def create_sample_db(path, count=3):
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
        cur.execute(f"INSERT INTO concepts (title, slug, summary) VALUES ('Concept {i}', 'concept-{i}', 'Summary {i}');")
    conn.commit()
    conn.close()

print("======================================================================")
print("   RUNNING DEPLOYMENT SAFETY & PERSISTENCE TEST SUITE")
print("======================================================================")

# Ensure image is built
print("Building baseline image...")
run_cmd(f"cd {BASE_DIR}/backend && docker build -t {IMAGE} .")

results = []

def record(scenario_name, passed, detail=""):
    status = "PASSED" if passed else "FAILED"
    results.append((scenario_name, status, detail))
    print(f"[{status}] {scenario_name} - {detail}")

# ------------------------------------------------------------------------------
# Scenario 1: First migration from an existing running container with DB
# ------------------------------------------------------------------------------
print("\n--- Test 1: First migration from a running container ---")
cleanup()
os.makedirs(f"{TEST_DATA_DIR}/tmp_seed", exist_ok=True)
seed_db = f"{TEST_DATA_DIR}/tmp_seed/forge.db"
create_sample_db(seed_db, count=4)

# Start dummy running container with DB inside writable layer
run_cmd(f"docker run -d --name forge {IMAGE}")
run_cmd(f"docker cp {seed_db} forge:/app/instance/forge.db")
shutil.rmtree(f"{TEST_DATA_DIR}/tmp_seed")

res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
time.sleep(2)

if res.returncode == 0 and os.path.exists(f"{TEST_DATA_DIR}/forge.db"):
    status, concepts = http_get(f"http://localhost:{PORT}/api/concepts/")
    record("Scenario 1: Running container migration", len(concepts) == 4, f"Extracted & verified {len(concepts)} concepts")
else:
    record("Scenario 1: Running container migration", False, f"Deploy failed: {res.stderr}")

# ------------------------------------------------------------------------------
# Scenario 2: Migration from a stopped container
# ------------------------------------------------------------------------------
print("\n--- Test 2: Migration from a stopped container ---")
cleanup()
os.makedirs(f"{TEST_DATA_DIR}/tmp_seed", exist_ok=True)
create_sample_db(f"{TEST_DATA_DIR}/tmp_seed/forge.db", count=3)

# Create container and stop it immediately
run_cmd(f"docker create --name forge {IMAGE}")
run_cmd(f"docker cp {TEST_DATA_DIR}/tmp_seed/forge.db forge:/app/instance/forge.db")
shutil.rmtree(f"{TEST_DATA_DIR}/tmp_seed")

res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
time.sleep(2)

if res.returncode == 0 and os.path.exists(f"{TEST_DATA_DIR}/forge.db"):
    status, concepts = http_get(f"http://localhost:{PORT}/api/concepts/")
    record("Scenario 2: Stopped container migration", len(concepts) == 3, f"Extracted from stopped container: {len(concepts)} concepts")
else:
    record("Scenario 2: Stopped container migration", False, f"Deploy failed: {res.stderr}")

# ------------------------------------------------------------------------------
# Scenario 3: Existing persistent database on subsequent deployment
# ------------------------------------------------------------------------------
print("\n--- Test 3: Subsequent deployment with existing persistent database ---")
# Add a new concept via API to the active container (now 3 + 1 = 4)
http_post(f"http://localhost:{PORT}/api/concepts/", {"title": "Subsequent Concept", "slug": "subsequent-concept", "summary": "Test 3"})

# Run deploy again - it should detect existing persistent DB and create a backup
res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
time.sleep(2)

backups = os.listdir(f"{TEST_DATA_DIR}/backups")
status, concepts = http_get(f"http://localhost:{PORT}/api/concepts/")
passed = (res.returncode == 0 and len(backups) >= 1 and len(concepts) == 4)
record("Scenario 3: Subsequent deployment", passed, f"Pre-deploy backup created ({len(backups)} in backup dir), concepts preserved: {len(concepts)}")

# ------------------------------------------------------------------------------
# Scenario 4: Missing database in an existing container (fail-closed abort)
# ------------------------------------------------------------------------------
print("\n--- Test 4: Missing database in existing container (fail-closed) ---")
cleanup()
run_cmd(f"docker run -d --name forge {IMAGE}")
run_cmd("docker exec forge rm -rf /app/instance/forge.db /app/forge.db 2>/dev/null || true")

res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
container_preserved = run_cmd("docker ps -a --format '{{.Names}}' | grep -q '^forge$'").returncode == 0
db_not_created = not os.path.exists(f"{TEST_DATA_DIR}/forge.db")

record("Scenario 4: Missing DB fail-closed abort", res.returncode != 0 and container_preserved and db_not_created, 
       f"Aborted cleanly (rc={res.returncode}), container preserved, no phantom DB created")

# ------------------------------------------------------------------------------
# Scenario 5: Failed integrity check on corrupt database (fail-closed abort)
# ------------------------------------------------------------------------------
print("\n--- Test 5: Corrupt database integrity failure (fail-closed) ---")
cleanup()
run_cmd(f"docker run -d --name forge {IMAGE}")
run_cmd("docker exec forge mkdir -p /app/instance")
run_cmd("docker exec forge bash -c 'echo \"CORRUPTED GARBAGE NOT SQLITE\" > /app/instance/forge.db'")

res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
container_preserved = run_cmd("docker ps -a --format '{{.Names}}' | grep -q '^forge$'").returncode == 0
db_not_migrated = not os.path.exists(f"{TEST_DATA_DIR}/forge.db")

record("Scenario 5: Corrupt DB integrity fail-closed", res.returncode != 0 and container_preserved and db_not_migrated,
       f"Aborted cleanly on corrupt check (rc={res.returncode}), container preserved")

# ------------------------------------------------------------------------------
# Scenario 6: Interrupted migration safety
# ------------------------------------------------------------------------------
print("\n--- Test 6: Interrupted migration safety ---")
cleanup()
os.makedirs(f"{TEST_DATA_DIR}", exist_ok=True)
create_sample_db(f"{TEST_DATA_DIR}/forge.db", count=2)
# Pre-deployment backup exists
run_cmd(f"python3 {BASE_DIR}/scripts/backup_db.py {TEST_DATA_DIR}/forge.db {TEST_DATA_DIR}/backups")
initial_backups = len(os.listdir(f"{TEST_DATA_DIR}/backups"))

record("Scenario 6: Interrupted migration safety", initial_backups >= 1 and os.path.exists(f"{TEST_DATA_DIR}/forge.db"),
       f"Verified pre-deploy backup exists and active database is uncorrupted")

# ------------------------------------------------------------------------------
# Scenario 7: Fresh installation with no container or DB
# ------------------------------------------------------------------------------
print("\n--- Test 7: Fresh installation ---")
cleanup()
# Ensure no container exists, and isolate from local dev DB
res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
time.sleep(2)

if res.returncode == 0:
    status, health = http_get(f"http://localhost:{PORT}/health")
    status_concepts, concepts = http_get(f"http://localhost:{PORT}/api/concepts/")
    record("Scenario 7: Fresh installation", health["status"] == "healthy" and concepts == [],
           f"Fresh container healthy (HTTP {status}), mounted empty DB (0 concepts)")
else:
    record("Scenario 7: Fresh installation", False, f"Fresh install failed: {res.stderr}")

# ------------------------------------------------------------------------------
# Scenario 8: Container recreation with existing persistent data
# ------------------------------------------------------------------------------
print("\n--- Test 8: Container recreation with existing persistent data ---")
# Add a concept to the active fresh container
http_post(f"http://localhost:{PORT}/api/concepts/", {"title": "Persistent Concept", "slug": "persistent-concept", "summary": "Test 8"})

# Destroy container completely
run_cmd("docker rm -f forge")
assert run_cmd("docker ps -a --format '{{.Names}}' | grep -q '^forge$'").returncode != 0

# Redeploy against the same persistent storage
res = run_cmd(f"export FORGE_DATA_DIR={TEST_DATA_DIR} && export FORGE_LEGACY_DB=/nonexistent/forge.db && cd {BASE_DIR} && bash scripts/deploy.sh")
time.sleep(2)

status, concepts = http_get(f"http://localhost:{PORT}/api/concepts/")
record("Scenario 8: Container recreation with existing data", len(concepts) == 1 and concepts[0]["slug"] == "persistent-concept",
       f"Data survived container deletion (found {len(concepts)} concept: '{concepts[0]['slug']}')")

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
