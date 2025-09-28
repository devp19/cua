#!/bin/bash

echo "Cleaning up Android Docker containers..."

# Stop and remove any android test containers
for container in android-quick-test android-test-container android-advanced-test android-ws-test android-container; do
    if docker ps -a | grep -q $container; then
        echo "Stopping and removing $container..."
        docker stop $container 2>/dev/null
        docker rm $container 2>/dev/null
    fi
done

echo "Current Docker containers:"
docker ps -a

echo ""
echo "Cleanup complete. You can now run the test."
