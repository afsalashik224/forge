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
LEGACY_DB="${FORGE_LEGACY_DB:-$FORGE_ROOT/backend/instance/forge.db}"

CONTAINER_NAME="forge"
BACKUP_CONTAINER_NAME="forge-previous"
PORT="${FORGE_PORT:-5000}"
HEALTH_CHECK_URL="${FORGE_HEALTH_CHECK_URL:-http://127.0.0.1:${PORT}/health}"

# Least-privilege permission policy:
# Directory: 775 (owner and group can create/delete WAL/SHM files; no world write)
# Database:  664 (owner and group can read/write; no world write)
mkdir -p "$BACKUP_DIR"
chmod 775 "$DATA_DIR" 2>/dev/null || true
chmod 775 "$BACKUP_DIR" 2>/dev/null || true

echo "Forge Root:       $FORGE_ROOT"
echo "Host Data Dir:    $DATA_DIR"
echo "Host Backups Dir: $BACKUP_DIR"
echo "Legacy Host DB:   $LEGACY_DB"

# ------------------------------------------------------------------------------
# 2. State Detection: Database, Container, and Ambiguity Check
# ------------------------------------------------------------------------------
HAS_PERSISTENT_DB=false
if [ -f "$DATA_DIR/forge.db" ]; then
    HAS_PERSISTENT_DB=true
fi

HAS_LEGACY_DB=false
if [ -f "$LEGACY_DB" ]; then
    HAS_LEGACY_DB=true
fi

CONTAINER_EXISTS=false
CONTAINER_WAS_RUNNING=false
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    CONTAINER_EXISTS=true
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        CONTAINER_WAS_RUNNING=true
    fi
fi

echo "State: persistent_db=$HAS_PERSISTENT_DB, container_exists=$CONTAINER_EXISTS (was_running=$CONTAINER_WAS_RUNNING), legacy_db=$HAS_LEGACY_DB"

# ------------------------------------------------------------------------------
# 3. Rollback Trap Definition
# ------------------------------------------------------------------------------
DEPLOYMENT_SUCCESS=false
NEW_CONTAINER_STARTED=false
CONTAINER_SWAPPED=false

cleanup_and_rollback() {
    local exit_code=$?
    trap - EXIT ERR INT TERM

    if [ "$DEPLOYMENT_SUCCESS" = true ]; then
        exit 0
    fi

    echo ""
    echo "========================================================================"
    echo "CRITICAL: Deployment failed or interrupted (code: $exit_code). Initiating rollback..."
    echo "========================================================================"

    # If staging directory was left behind, clean it up
    rm -rf "$STAGING_DIR" 2>/dev/null || true

    # If new container was started or created during swap, inspect and remove it
    if [ "$CONTAINER_SWAPPED" = true ]; then
        if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
            echo "Logs from failed container '${CONTAINER_NAME}':"
            docker logs --tail 30 "$CONTAINER_NAME" 2>/dev/null || true
            echo "Removing failed container '${CONTAINER_NAME}'..."
            docker stop "$CONTAINER_NAME" 2>/dev/null || true
            docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
        fi
    fi

    # If previous container was renamed to forge-previous, restore it
    if docker ps -a --format '{{.Names}}' | grep -q "^${BACKUP_CONTAINER_NAME}$"; then
        echo "Restoring previous container '${BACKUP_CONTAINER_NAME}' to '${CONTAINER_NAME}'..."
        docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
        docker rename "$BACKUP_CONTAINER_NAME" "$CONTAINER_NAME"

        if [ "$CONTAINER_WAS_RUNNING" = true ]; then
            echo "Restarting restored container '${CONTAINER_NAME}'..."
            docker start "$CONTAINER_NAME" 2>/dev/null || true
            echo "Previous container is running."
        else
            echo "Previous container restored as '${CONTAINER_NAME}' (kept stopped, matching original state)."
        fi
    fi

    echo "Rollback completed. Deployment aborted safely."
    exit "${exit_code:-1}"
}

trap cleanup_and_rollback EXIT ERR INT TERM

# ------------------------------------------------------------------------------
# 4. Database Safety, Extraction & Migration
# ------------------------------------------------------------------------------
if [ "$HAS_PERSISTENT_DB" = true ]; then
    echo "Active persistent database found at: $DATA_DIR/forge.db"
    echo "Creating timestamped pre-deployment backup and verifying integrity..."
    python3 scripts/backup_db.py "$DATA_DIR/forge.db" "$BACKUP_DIR"
    chmod 664 "$DATA_DIR/forge.db" 2>/dev/null || true
    echo "Persistent database verified successfully."

else
    # Persistent DB does not exist yet. We must migrate or fresh-install.
    CONTAINER_HAS_DB=false
    FOUND_CONTAINER_DB=""
    if [ "$CONTAINER_EXISTS" = true ]; then
        mkdir -p "$STAGING_DIR"
        rm -rf "$STAGING_DIR"/*
        for candidate in "/app/instance/forge.db" "/app/forge.db"; do
            if docker cp "${CONTAINER_NAME}:${candidate}" "$STAGING_DIR/" 2>/dev/null; then
                if [ -f "$STAGING_DIR/forge.db" ]; then
                    CONTAINER_HAS_DB=true
                    FOUND_CONTAINER_DB="$STAGING_DIR/forge.db"
                    break
                fi
            fi
        done
    fi

    # Ambiguity check: fail closed if both container DB and host legacy DB exist
    if [ "$CONTAINER_HAS_DB" = true ] && [ "$HAS_LEGACY_DB" = true ]; then
        if [ "$FORGE_MIGRATION_SOURCE" = "container" ]; then
            echo "Explicit FORGE_MIGRATION_SOURCE=container selected."
            HAS_LEGACY_DB=false
        elif [ "$FORGE_MIGRATION_SOURCE" = "legacy" ]; then
            echo "Explicit FORGE_MIGRATION_SOURCE=legacy selected."
            CONTAINER_HAS_DB=false
        else
            echo "CRITICAL ERROR: Ambiguous migration source!"
            echo "Both container '${CONTAINER_NAME}' (containing database) and host legacy DB '${LEGACY_DB}' exist,"
            echo "but no persistent database exists at '${DATA_DIR}/forge.db'."
            echo "Refusing to guess which database contains the authoritative production data."
            echo "Specify FORGE_MIGRATION_SOURCE=container or FORGE_MIGRATION_SOURCE=legacy to proceed."
            rm -rf "$STAGING_DIR" 2>/dev/null || true
            exit 1
        fi
    fi

    if [ "$CONTAINER_EXISTS" = true ]; then
        echo "Detected existing '${CONTAINER_NAME}' container without host persistent database."
        if [ "$CONTAINER_HAS_DB" != true ]; then
            echo "CRITICAL ERROR: Existing container '${CONTAINER_NAME}' has no recognized database."
            echo "Aborting deployment fail-closed to prevent accidental loss or misconfiguration."
            rm -rf "$STAGING_DIR" 2>/dev/null || true
            exit 1
        fi

        # Stop container gracefully if running to ensure SQLite write flush
        if [ "$CONTAINER_WAS_RUNNING" = true ]; then
            echo "Gracefully stopping container '${CONTAINER_NAME}' to flush in-flight SQLite writes..."
            docker stop "$CONTAINER_NAME"
        fi

        # Re-copy after stop to ensure flushed WAL/SHM data
        rm -rf "$STAGING_DIR"/*
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

        echo "Migrating database from container snapshot: $FOUND_CONTAINER_DB"
        python3 scripts/migrate_to_persistent_storage.py "$FOUND_CONTAINER_DB" "$DATA_DIR"
        rm -rf "$STAGING_DIR" 2>/dev/null || true
        chmod 664 "$DATA_DIR/forge.db" 2>/dev/null || true
        echo "Container database migration to $DATA_DIR/forge.db completed successfully."

    elif [ "$HAS_LEGACY_DB" = true ]; then
        echo "Found host legacy database at $LEGACY_DB. Migrating to $DATA_DIR..."
        python3 scripts/migrate_to_persistent_storage.py "$LEGACY_DB" "$DATA_DIR"
        chmod 664 "$DATA_DIR/forge.db" 2>/dev/null || true
        echo "Legacy database migration to $DATA_DIR/forge.db completed successfully."

    else
        echo "Fresh install detected: no existing database or container found."
        echo "New database will be initialized in persistent storage at: $DATA_DIR/forge.db"
    fi
fi

# ------------------------------------------------------------------------------
# 5. Build Image
# ------------------------------------------------------------------------------
cd "$FORGE_ROOT/backend"
echo "Building Docker image..."
docker build -t forge-backend .

# If fresh install or persistent database file does not exist yet, initialize schema
if [ ! -f "$DATA_DIR/forge.db" ]; then
    echo "Initializing new database schema in persistent storage at $DATA_DIR/forge.db..."
    docker run --rm -v "$DATA_DIR:/app/instance" forge-backend python3 -c "import os; from app import create_app; from app.database.db import db; app = create_app(); app.app_context().push(); db.create_all(); os.chmod('/app/instance/forge.db', 0o664)"
    chmod 664 "$DATA_DIR/forge.db" 2>/dev/null || true
    echo "Schema initialization complete."
fi

# ------------------------------------------------------------------------------
# 6. Safe Container Swap
# ------------------------------------------------------------------------------
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping and preserving existing container as '${BACKUP_CONTAINER_NAME}'..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm -f "$BACKUP_CONTAINER_NAME" 2>/dev/null || true
    docker rename "$CONTAINER_NAME" "$BACKUP_CONTAINER_NAME"
    CONTAINER_SWAPPED=true
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
NEW_CONTAINER_STARTED=true
docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    -p "${PORT}:5000" \
    -v "$DATA_DIR:/app/instance" \
    $ENV_ARGS \
    forge-backend

# Ensure permissions on host data directory and db file
chmod 775 "$DATA_DIR" 2>/dev/null || true
chmod 664 "$DATA_DIR"/forge.db* 2>/dev/null || true

# ------------------------------------------------------------------------------
# 7. Post-Deployment Verification
# ------------------------------------------------------------------------------
echo "Verifying new container health..."
HEALTHY=false
for i in {1..15}; do
    if curl -s -f "$HEALTH_CHECK_URL" >/dev/null 2>&1; then
        HEALTHY=true
        break
    fi
    sleep 1
done

if [ "$HEALTHY" != true ]; then
    echo "CRITICAL ERROR: New container failed health check at $HEALTH_CHECK_URL!"
    exit 1
fi

echo "New container passed health check."

# Verify API data endpoint if persistent database exists
if [ -f "$DATA_DIR/forge.db" ]; then
    if ! curl -s -f "http://127.0.0.1:${PORT}/api/concepts/" >/dev/null 2>&1; then
        echo "CRITICAL ERROR: API data endpoint failed verification!"
        exit 1
    fi
    echo "API data endpoint verified successfully."
fi

# Verification passed: mark deployment successful
DEPLOYMENT_SUCCESS=true

# Clean up previous container now that new container is 100% verified
if docker ps -a --format '{{.Names}}' | grep -q "^${BACKUP_CONTAINER_NAME}$"; then
    echo "Removing previous container '${BACKUP_CONTAINER_NAME}'..."
    docker rm -f "$BACKUP_CONTAINER_NAME" 2>/dev/null || true
fi

echo "=== Deployment Successfully Completed ==="
echo "Database securely persisted at: $DATA_DIR/forge.db"
exit 0
