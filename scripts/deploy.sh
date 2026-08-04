#!/bin/bash

set -e

echo "=== Deploying Forge ==="

cd ~/forge/backend

echo "Working directory:"
pwd

echo "Stopping old container..."
docker stop forge || true

echo "Removing old container..."
docker rm forge || true

echo "Building Docker image..."
docker build -t forge-backend .

echo "Starting new container..."
docker run -d \
    --name forge \
    --restart unless-stopped \
    -p 5000:5000 \
    forge-backend

echo "Deployment completed."
