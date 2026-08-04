#!/bin/bash

set -e

echo "=== Deploying Forge ==="

cd ~/forge

echo "Pulling latest code..."
git pull origin main

cd backend

echo "Stopping old container..."
docker stop forge || true

echo "Removing old container..."
docker rm forge || true

echo "Building Docker image..."
docker build -t forge-backend .

echo "Starting new container..."
docker run -d \
  --name forge \
  -p 5000:5000 \
  forge-backend

echo "Deployment completed."
