#!/usr/bin/env python3
"""
Test Docker SQLite persistence across container removal and recreation.
"""

import json
import os
import shutil
import sqlite3
import subprocess
import time
import urllib.request

HOST_DATA_DIR = "/home/afsal/forge_docker_test_data"
PORT = 5005
IMAGE = "forge-backend:test"
SRC_DB = "/mnt/d/forge/backend/instance/forge.db"

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Command stderr: {res.stderr.strip()}")
    return res

def http_get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        return response.status, json.loads(response.read().decode())

def http_post(url, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        return response.status, json.loads(response.read().decode())

print("=== Starting Docker Persistence Demonstration ===")

# Step 0: Clean up and initialize test data directory
run_cmd("docker stop forge-test-1 forge-test-2 2>/dev/null || true")
run_cmd("docker rm forge-test-1 forge-test-2 2>/dev/null || true")
if os.path.exists(HOST_DATA_DIR):
    shutil.rmtree(HOST_DATA_DIR)
os.makedirs(HOST_DATA_DIR, exist_ok=True)

# Migrate source database to test data directory
import sys
sys.path.insert(0, "/mnt/d/forge/scripts")
from migrate_to_persistent_storage import verify_and_migrate
verify_and_migrate(SRC_DB, HOST_DATA_DIR)

# Set permissions so container can write to mounted dir
os.chmod(HOST_DATA_DIR, 0o777)
if os.path.exists(os.path.join(HOST_DATA_DIR, "forge.db")):
    os.chmod(os.path.join(HOST_DATA_DIR, "forge.db"), 0o666)

# Step 1: Start Container 1
print(f"\n[Step 1] Starting Container 1 ('forge-test-1') mounting {HOST_DATA_DIR} to /app/instance...")
run_cmd(f"docker run -d --name forge-test-1 -p {PORT}:5000 -v {HOST_DATA_DIR}:/app/instance {IMAGE}")
time.sleep(3)

# Check health
status, health = http_get(f"http://localhost:{PORT}/health")
print(f"  Container 1 Health: HTTP {status} -> {health['status']}")

# Check existing concepts
status, concepts = http_get(f"http://localhost:{PORT}/api/concepts/")
print(f"  Container 1 Initial Concepts Count: {len(concepts)}")
for c in concepts:
    print(f"    - [{c['id']}] {c['title']} ({c['slug']})")

assert len(concepts) == 4, f"Expected 4 initial concepts, got {len(concepts)}"

# Step 3: Add new concept in Container 1
print("\n[Step 2] Adding 5th concept to Container 1 via POST /api/concepts/...")
new_concept = {
    "title": "Persistent Container Storage",
    "slug": "persistent-container-storage",
    "summary": "Demonstrating that SQLite records survive docker rm."
}
status, created = http_post(f"http://localhost:{PORT}/api/concepts/", new_concept)
print(f"  Created concept: HTTP {status} -> ID #{created['data']['id']} ({created['data']['title']})")

status, concepts_after = http_get(f"http://localhost:{PORT}/api/concepts/")
print(f"  Container 1 Concept Count after creation: {len(concepts_after)}")
assert len(concepts_after) == 5, f"Expected 5 concepts, got {len(concepts_after)}"

# Step 4: Destroy Container 1 completely
print("\n[Step 3] DESTROYING Container 1 ('docker stop' and 'docker rm')...")
run_cmd("docker stop forge-test-1")
run_cmd("docker rm forge-test-1")

res = run_cmd("docker ps -a --filter name=forge-test-1 --format '{{.Names}}'")
print(f"  Verifying Container 1 is deleted: '{res.stdout.strip()}' (empty means fully removed)")

# Step 5: Start Container 2 (Brand New Container)
print("\n[Step 4] Starting brand new Container 2 ('forge-test-2') with the same volume mount...")
run_cmd(f"docker run -d --name forge-test-2 -p {PORT}:5000 -v {HOST_DATA_DIR}:/app/instance {IMAGE}")
time.sleep(3)

status, health2 = http_get(f"http://localhost:{PORT}/health")
print(f"  Container 2 Health: HTTP {status} -> {health2['status']}")

# Step 6: Verify all records exist in Container 2!
print("\n[Step 5] Querying concepts from Container 2...")
status, concepts_c2 = http_get(f"http://localhost:{PORT}/api/concepts/")
print(f"  Container 2 Concepts Count: {len(concepts_c2)}")
for c in concepts_c2:
    print(f"    - [{c['id']}] {c['title']} ({c['slug']})")

assert len(concepts_c2) == 5, f"Expected 5 concepts in Container 2, got {len(concepts_c2)}"
slugs = [c["slug"] for c in concepts_c2]
assert "persistent-container-storage" in slugs, "New concept was lost!"

print("\n=== PERSISTENCE DEMONSTRATION PASSED ===")
print("All 5 concepts (including original 4 and newly inserted 5th) survived container deletion and recreation!")

# Cleanup test container
print("\nCleaning up test container...")
run_cmd("docker stop forge-test-2")
run_cmd("docker rm forge-test-2")
print("Done.")
