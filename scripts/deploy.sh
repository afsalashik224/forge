#!/bin/bash

set -e

echo "=== Forge Production Deployment & Database Protection ==="

# ------------------------------------------------------------------------------
# 1. Environment & Paths Configuration
# ------------------------------------------------------------------------------
FORGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$FORGE_ROOT"

DATA_DIR="${FORGE_DATA_DIR:-$HOME/forge/data}"
BACKUP_DIR="$DATA_DIR/backups"
STAGING_DIR="$DATA_DIR/staging"

mkdir -p "$BACKUP_DIR"
chmod 755 "$DATA_DIR"

CONTAINER_NAME="forge"
BACKUP_CONTAINER_NAME="forge-previous"
PORT=5000

echo "Forge Root:       $FORGE_ROOT"
echo "Host Data Dir:    $DATA_DIR"
echo "Host Backups Dir: $BACKUP_DIR"

# ------------------------------------------------------------------------------
# 2. State Detection: Database, Container, and Fresh-Install
# ------------------------------------------------------------------------------
HAS_PERSISTENT_DB=false
if [ -f "$DATA_DIR/forge.db" ]; then
    HAS_PERSISTENT_DB=true
fi

CONTAINER_EXISTS=false
CONTAINER_RUNNING=false
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    CONTAINER_EXISTS=true
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        CONTAINER_RUNNING=true
    fi
fi

echo "State: persistent_db=$HAS_PERSISTENT_DB, container_exists=$CONTAINER_EXISTS, container_running=$CONTAINER_RUNNING"

# ------------------------------------------------------------------------------
# 3. Database Safety, Extraction & Migration
# ------------------------------------------------------------------------------
if [ "$HAS_PERSISTENT_DB" = true ]; then
    # Subsequent deployment: active persistent database already exists on host.
    echo "Existing persistent database found at: $DATA_DIR/forge.db"
    echo "Creating timestamped pre-deployment backup..."
    python3 scripts/backup_db.py "$DATA_DIR/forge.db" "$BACKUP_DIR"
    echo "Pre-deployment backup verified."

elif [ "$CONTAINER_EXISTS" = true ]; then
    # First deployment migration: database is trapped in existing container writable layer.
    echo "Detected existing '${CONTAINER_NAME}' container without host persistent database."
    echo "Initiating safe, non-destructive container database extraction..."

    # Step 3.1: Graceful stop (if running) so SQLite flushes locks and commits
    if [ "$CONTAINER_RUNNING" = true ]; then
        echo "Gracefully stopping container '${CONTAINER_NAME}' to flush in-flight SQLite writes..."
        docker stop "$CONTAINER_NAME"
    else
        echo "Container '${CONTAINER_NAME}' is already stopped."
    fi

    # Step 3.2: Extract database and potential WAL/SHM files safely via docker cp
    mkdir -p "$STAGING_DIR"
    rm -rf "$STAGING_DIR"/*

    FOUND_CONTAINER_DB=""
    # Check known candidate locations inside container
    for candidate in "/app/instance" "/app/forge.db"; do
        if docker cp "${CONTAINER_NAME}:${candidate}" "$STAGING_DIR/" 2>/dev/null; then
            if [ -f "$STAGING_DIR/instance/forge.db" ]; then
                FOUND_CONTAINER_DB="$STAGING_DIR/instance/forge.db"
                break
            elif [ -f "$STAGING_DIR/forge.db" ]; then
                FOUND_CONTAINER_DB="$STAGING_DIR/forge.db"
                break
            fi
        fi
    done

    # Step 3.3: Fail-closed verification
    if [ -z "$FOUND_CONTAINER_DB" ] || [ ! -f "$FOUND_CONTAINER_DB" ]; then
        echo "CRITICAL ERROR: Existing container '${CONTAINER_NAME}' has no recognized database."
        echo "Aborting deployment fail-closed to prevent accidental loss or misconfiguration."
        rm -rf "$STAGING_DIR"
        exit 1
    fi

    echo "Successfully extracted database snapshot from container: $FOUND_CONTAINER_DB"

    # Step 3.4: Integrity verification and migration to persistent host storage
    echo "Verifying integrity, creating timestamped backup, and migrating to host storage..."
    python3 scripts/migrate_to_persistent_storage.py "$FOUND_CONTAINER_DB" "$DATA_DIR"
    rm -rf "$STAGING_DIR"
    chmod 666 "$DATA_DIR/forge.db" 2>/dev/null || true
    echo "Container database migration to $DATA_DIR/forge.db completed successfully."

LEGACY_DB="${FORGE_LEGACY_DB:-$FORGE_ROOT/backend/instance/forge.db}"
elif [ -f "$LEGACY_DB" ]; then
    # Legacy host file migration (if host backend/instance/forge.db exists)
    echo "Found host legacy database at $LEGACY_DB. Migrating to $DATA_DIR..."
    python3 scripts/migrate_to_persistent_storage.py "$LEGACY_DB" "$DATA_DIR"
    chmod 666 "$DATA_DIR/forge.db" 2>/dev/null || true

else
    # Fresh installation
    echo "Fresh install detected: no existing database or container found."
    echo "New database will be initialized in persistent storage at: $DATA_DIR/forge.db"
fi

# ------------------------------------------------------------------------------
# 4. Safe Container Swap with Zero-Loss Rollback Guarantee
# ------------------------------------------------------------------------------
cd "$FORGE_ROOT/backend"

echo "Building Docker image..."
docker build -t forge-backend .

# If fresh install or persistent database file does not exist yet, initialize schema
if [ ! -f "$DATA_DIR/forge.db" ]; then
    echo "Initializing new database schema in persistent storage at $DATA_DIR/forge.db..."
    docker run --rm -v "$DATA_DIR:/app/instance" forge-backend python3 -c "import os; from app import create_app; from app.database.db import db; app = create_app(); app.app_context().push(); db.create_all(); os.chmod('/app/instance/forge.db', 0o666)"
    chmod 666 "$DATA_DIR/forge.db" 2>/dev/null || true
    echo "Schema initialization complete."
fi

# If an old container exists, stop it to release port and rename it as backup
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping and preserving existing container as '${BACKUP_CONTAINER_NAME}' until new container passes verification..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm -f "$BACKUP_CONTAINER_NAME" 2>/dev/null || true
    docker rename "$CONTAINER_NAME" "$BACKUP_CONTAINER_NAME"
fi

# Determine environment arguments
ENV_ARGS=""
if [ -f .env ]; then
    echo "Using host .env configuration file."
    ENV_ARGS="--env-file .env"
else
    echo "Notice: No .env file found in $(pwd). Container will use defaults."
fi

echo "Starting new container with persistent host storage mount..."
docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    -p "${PORT}:5000" \
    -v "$DATA_DIR:/app/instance" \
    $ENV_ARGS \
    forge-backend

# ------------------------------------------------------------------------------
# 5. Post-Deployment Health & Data Verification
# ------------------------------------------------------------------------------
echo "Verifying new container health..."
HEALTHY=false
for i in {1..15}; do
    if curl -s -f "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
        HEALTHY=true
        break
    fi
    sleep 1
done

if [ "$HEALTHY" = true ]; then
    echo "New container passed health check on port ${PORT}."
    
    # If persistent DB exists, verify that API serves data
    if [ -f "$DATA_DIR/forge.db" ]; then
        if curl -s -f "http://127.0.0.1:${PORT}/api/concepts/" >/dev/null 2>&1; then
            echo "API data endpoint verified successfully."
        fi
    fi

    # Only now that the new container is verified healthy do we clean up the previous container
    if docker ps -a --format '{{.Names}}' | grep -q "^${BACKUP_CONTAINER_NAME}$"; then
        echo "Removing previous container '${BACKUP_CONTAINER_NAME}'..."
        docker rm -f "$BACKUP_CONTAINER_NAME" 2>/dev/null || true
    fi
    echo "=== Deployment Successfully Completed ==="
    echo "Database securely persisted at: $DATA_DIR/forge.db"
    exit 0
else
    echo "CRITICAL ERROR: New container failed health check!"
    echo "Initiating automatic rollback to previous container..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

    if docker ps -a --format '{{.Names}}' | grep -q "^${BACKUP_CONTAINER_NAME}$"; then
        docker rename "$BACKUP_CONTAINER_NAME" "$CONTAINER_NAME"
        docker start "$CONTAINER_NAME"
        echo "Rollback complete: previous container restored and started."
    fi
    exit 1
fi
