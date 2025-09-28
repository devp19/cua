#!/bin/bash

# Debug script for Android Docker Provider
echo "========================================="
echo "Android Docker Provider Debug Script"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "\n${YELLOW}1. Checking Docker...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker installed${NC}"
    docker --version
    
    # Check if Docker daemon is running
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✓ Docker daemon running${NC}"
    else
        echo -e "${RED}✗ Docker daemon not running${NC}"
        echo "  Please start Docker Desktop or Docker daemon"
        exit 1
    fi
else
    echo -e "${RED}✗ Docker not installed${NC}"
    exit 1
fi

echo -e "\n${YELLOW}2. Checking for Android container...${NC}"
CONTAINER_NAME="android-test-container"
if docker ps -a | grep -q $CONTAINER_NAME; then
    echo -e "${GREEN}✓ Found container: $CONTAINER_NAME${NC}"
    
    # Check if it's running
    if docker ps | grep -q $CONTAINER_NAME; then
        echo -e "${GREEN}  Status: Running${NC}"
    else
        echo -e "${YELLOW}  Status: Stopped${NC}"
        echo "  Starting container..."
        docker start $CONTAINER_NAME
    fi
else
    echo -e "${YELLOW}✗ No Android container found${NC}"
fi

echo -e "\n${YELLOW}3. Checking Android image...${NC}"
if docker images | grep -q "budtmo/docker-android"; then
    echo -e "${GREEN}✓ Android image found${NC}"
    docker images | grep "budtmo/docker-android"
else
    echo -e "${YELLOW}✗ Android image not found${NC}"
    echo "  To pull the image, run:"
    echo "  docker pull budtmo/docker-android:emulator_11.0"
fi

echo -e "\n${YELLOW}4. Checking ports...${NC}"
PORTS=(8000 6080 5555 5554 5900)
for PORT in "${PORTS[@]}"; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Port $PORT is in use${NC}"
        lsof -i :$PORT | head -2
    else
        echo -e "${GREEN}✓ Port $PORT is available${NC}"
    fi
done

echo -e "\n${YELLOW}5. Testing container connectivity (if running)...${NC}"
if docker ps | grep -q $CONTAINER_NAME; then
    # Test ADB
    echo "  Testing ADB in container..."
    if docker exec $CONTAINER_NAME adb devices 2>/dev/null | grep -q "device"; then
        echo -e "${GREEN}  ✓ ADB working${NC}"
        docker exec $CONTAINER_NAME adb devices
    else
        echo -e "${YELLOW}  ⚠ ADB not ready yet${NC}"
    fi
    
    # Test API server
    echo "  Testing API server..."
    if curl -s http://localhost:8000/health 2>/dev/null | grep -q "ready"; then
        echo -e "${GREEN}  ✓ API server responding${NC}"
    else
        echo -e "${YELLOW}  ⚠ API server not responding${NC}"
        echo "    The provider should install and start it automatically"
    fi
fi

echo -e "\n${YELLOW}6. Container logs (if running)...${NC}"
if docker ps | grep -q $CONTAINER_NAME; then
    echo "Last 20 lines of container logs:"
    docker logs --tail 20 $CONTAINER_NAME 2>&1 | sed 's/^/  /'
fi

echo -e "\n========================================="
echo -e "${GREEN}Debug complete!${NC}"
echo ""
echo "To run a test:"
echo "  python test_android_quick.py"
echo ""
echo "To view Android screen in browser:"
echo "  http://localhost:6080"
echo ""
echo "To manually interact with container:"
echo "  docker exec -it $CONTAINER_NAME bash"
echo "========================================="
