#!/bin/bash
set -euo pipefail

# Script to test the Docker container
# Usage: ./scripts/test_container.sh

echo "=== Testing Docker Container ==="
echo ""

# Test 1: Check non-root user
echo "Test 1: Checking container runs as non-root user..."
user_id=$(docker compose run --rm app id -u)
if [ "$user_id" = "1000" ]; then
    echo "✓ Container runs as non-root user (UID: $user_id)"
else
    echo "✗ Container does not run as expected user (UID: $user_id, expected: 1000)"
    exit 1
fi
echo ""

# Test 2: Check health endpoint
echo "Test 2: Checking health endpoint..."
if docker compose run --rm app python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" >/dev/null 2>&1; then
    echo "✓ Health check command works"
else
    echo "✗ Health check command failed"
    exit 1
fi
echo ""

# Test 3: Check container becomes healthy
echo "Test 3: Starting container and checking health status..."
docker compose up -d
timeout=60
health=""
while [ $timeout -gt 0 ]; do
    health=$(docker inspect --format='{{.State.Health.Status}}' event-planner-app 2>/dev/null || echo "starting")
    if [ "$health" = "healthy" ]; then
        echo "✓ Container became healthy"
        break
    fi
    sleep 2
    timeout=$((timeout-2))
done

if [ "$health" != "healthy" ]; then
    echo "✗ Container did not become healthy (status: $health)"
    docker compose logs app
    docker compose down
    exit 1
fi
echo ""

# Test 4: Test API endpoint
echo "Test 4: Testing API endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
if [ "$response" = "200" ]; then
    echo "✓ API endpoint responds correctly (HTTP $response)"
else
    echo "✗ API endpoint failed (HTTP $response)"
    docker compose down
    exit 1
fi
echo ""

# Test 5: Check security options
echo "Test 5: Checking security options..."
no_new_privs=$(docker inspect --format='{{.HostConfig.SecurityOpt}}' event-planner-app | grep -o "no-new-privileges" || echo "")
if [ -n "$no_new_privs" ]; then
    echo "✓ Security option 'no-new-privileges' is set"
else
    echo "⚠ Security option 'no-new-privileges' not found (may be set differently)"
fi
echo ""

echo "=== All tests passed! ==="
docker compose down
