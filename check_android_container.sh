#!/bin/bash

echo "Checking Android container status..."
echo "=================================="

CONTAINER="android-direct-test"

echo "1. Container status:"
docker ps | grep $CONTAINER

echo ""
echo "2. ADB devices in container:"
docker exec $CONTAINER adb devices

echo ""
echo "3. Emulator process:"
docker exec $CONTAINER ps aux | grep emulator

echo ""
echo "4. Container logs (last 20 lines):"
docker logs --tail 20 $CONTAINER

echo ""
echo "5. Check if emulator is booting:"
docker exec $CONTAINER getprop sys.boot_completed 2>/dev/null || echo "Emulator not ready"

echo ""
echo "6. Port mappings:"
docker port $CONTAINER

echo ""
echo "=================================="
echo "To monitor emulator boot:"
echo "  watch 'docker exec $CONTAINER adb devices'"
echo ""
echo "To see full logs:"
echo "  docker logs -f $CONTAINER"
