#!/bin/bash
set -euo pipefail

# Script to build and run the Docker container
# Usage: ./scripts/run.sh

echo "Building Docker image..."
docker compose build

echo "Starting services..."
docker compose up -d

echo "Waiting for service to be healthy..."
timeout=60
while [ $timeout -gt 0 ]; do
    health=$(docker inspect --format='{{.State.Health.Status}}' event-planner-app 2>/dev/null || echo "starting")
    if [ "$health" = "healthy" ]; then
        echo "✓ Service is healthy"
        break
    fi
    echo "Waiting for service to become healthy... ($health)"
    sleep 5
    timeout=$((timeout-5))
done

if [ "$health" != "healthy" ]; then
    echo "✗ Service did not become healthy within timeout"
    docker compose logs app
    exit 1
fi

echo "Service is running at http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo "Health check: http://localhost:8000/health"
echo ""
echo "To view logs: docker compose logs -f app"
echo "To stop: docker compose down"
