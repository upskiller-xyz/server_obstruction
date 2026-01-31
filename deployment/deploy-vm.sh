#!/bin/bash
#
# Deployment script for Obstruction Server on VM
# This script rebuilds and restarts the Docker container with optimized settings
#

set -e  # Exit on error

echo "=================================================="
echo "  Obstruction Server - VM Deployment"
echo "=================================================="

# Change to deployment directory
cd "$(dirname "$0")"

echo ""
echo "[1/5] Stopping existing containers..."
docker-compose down || true

echo ""
echo "[2/5] Removing old images to force rebuild..."
docker-compose rm -f obstruction-server || true
docker rmi obstruction-server:latest 2>/dev/null || true

echo ""
echo "[3/5] Building new image with optimizations..."
docker-compose build --no-cache obstruction-server

echo ""
echo "[4/5] Starting optimized container..."
docker-compose up -d obstruction-server

echo ""
echo "[5/5] Waiting for service to be ready..."
sleep 5

echo ""
echo "=================================================="
echo "  Deployment Configuration"
echo "=================================================="
docker-compose exec obstruction-server sh -c 'echo "Workers: $WORKERS"'
docker-compose exec obstruction-server sh -c 'echo "Threads: $THREADS"'
docker-compose exec obstruction-server sh -c 'echo "Log Level: $LOG_LEVEL"'

echo ""
echo "=================================================="
echo "  Service Status"
echo "=================================================="
docker-compose ps

echo ""
echo "Deployment complete!"
echo ""
echo "View logs with:"
echo "  docker logs -f obstruction-service"
echo ""
echo "Check health with:"
echo "  curl http://localhost:8081/"
echo ""
