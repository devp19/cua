#!/usr/bin/env python3
"""
Manual Bridge Test - Step by step debugging
"""

import subprocess
import time
import sys

CONTAINER = "android-ws-test"

def run_cmd(cmd, show_output=True):
    """Run command and show output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if show_output:
        if result.stdout:
            print(f"  stdout: {result.stdout}")
        if result.stderr:
            print(f"  stderr: {result.stderr}")
    print(f"  return code: {result.returncode}")
    return result

print("=" * 70)
print("MANUAL BRIDGE TEST")
print("=" * 70)

# Step 1: Check container exists
print("\n1. Checking if container exists...")
result = run_cmd(["docker", "ps", "-a", "--filter", f"name={CONTAINER}", "--format", "{{.Names}}"], show_output=False)
if CONTAINER not in result.stdout:
    print(f"ERROR: Container {CONTAINER} not found!")
    print("Please run: python test_android_websocket.py")
    sys.exit(1)
print(f"✓ Container {CONTAINER} exists")

# Step 2: Check if running
print("\n2. Checking if container is running...")
result = run_cmd(["docker", "ps", "--filter", f"name={CONTAINER}", "--format", "{{.Names}}"], show_output=False)
if CONTAINER not in result.stdout:
    print(f"ERROR: Container {CONTAINER} is not running!")
    sys.exit(1)
print(f"✓ Container is running")

# Step 3: Check if bridge script exists
print("\n3. Checking if bridge script exists...")
result = run_cmd(["docker", "exec", CONTAINER, "ls", "-la", "/tmp/computer_server.py"])
if result.returncode != 0:
    print("ERROR: Bridge script not found!")
    sys.exit(1)
print("✓ Bridge script exists")

# Step 4: Check Python version
print("\n4. Checking Python version in container...")
run_cmd(["docker", "exec", CONTAINER, "python3", "--version"])

# Step 5: Check if websockets is installed
print("\n5. Checking if websockets module is installed...")
result = run_cmd(["docker", "exec", CONTAINER, "python3", "-c", "import websockets; print(websockets.__version__)"])
if result.returncode != 0:
    print("✗ websockets NOT installed, installing now...")
    run_cmd(["docker", "exec", CONTAINER, "pip3", "install", "websockets"])
    # Try again
    result = run_cmd(["docker", "exec", CONTAINER, "python3", "-c", "import websockets; print(websockets.__version__)"])
    if result.returncode != 0:
        print("ERROR: Could not install websockets!")
        sys.exit(1)
print("✓ websockets is installed")

# Step 6: Try to run the bridge script to see errors
print("\n6. Testing bridge script for syntax errors...")
result = run_cmd(["docker", "exec", CONTAINER, "python3", "-m", "py_compile", "/tmp/computer_server.py"])
if result.returncode != 0:
    print("ERROR: Bridge script has syntax errors!")
    sys.exit(1)
print("✓ No syntax errors")

# Step 7: Kill any existing bridge process
print("\n7. Killing any existing bridge process...")
run_cmd(["docker", "exec", CONTAINER, "pkill", "-f", "computer_server.py"], show_output=False)
time.sleep(1)

# Step 8: Try to start bridge in foreground to see errors
print("\n8. Starting bridge in foreground (will show errors)...")
print("   Press Ctrl+C after a few seconds to stop...")
try:
    result = subprocess.run(
        ["docker", "exec", CONTAINER, "python3", "/tmp/computer_server.py", CONTAINER],
        timeout=5
    )
except subprocess.TimeoutExpired:
    print("   Bridge is running (timed out as expected)")
except KeyboardInterrupt:
    print("   Stopped by user")

# Step 9: Start in background
print("\n9. Starting bridge in background...")
run_cmd(["docker", "exec", "-d", CONTAINER, "python3", "/tmp/computer_server.py", CONTAINER])
time.sleep(2)

# Step 10: Check if process is running
print("\n10. Checking if bridge process is running...")
result = run_cmd(["docker", "exec", CONTAINER, "ps", "aux"], show_output=False)
if "computer_server.py" in result.stdout:
    print("✓ Bridge process is running!")
    for line in result.stdout.split('\n'):
        if 'computer_server.py' in line:
            print(f"   {line}")
else:
    print("✗ Bridge process is NOT running!")
    print("\nChecking logs...")
    run_cmd(["docker", "exec", CONTAINER, "cat", "/tmp/computer_server.log"])

# Step 11: Check if port is listening
print("\n11. Checking if port 8000 is listening...")
result = run_cmd(["docker", "exec", CONTAINER, "netstat", "-tuln"], show_output=False)
if ":8000" in result.stdout:
    print("✓ Port 8000 is listening!")
    for line in result.stdout.split('\n'):
        if ':8000' in line:
            print(f"   {line}")
else:
    print("✗ Port 8000 is NOT listening!")
    print("Full netstat output:")
    print(result.stdout)

# Step 12: Test WebSocket connection
print("\n12. Testing WebSocket connection from host...")
try:
    import websockets
    import asyncio
    import json
    
    async def test():
        uri = "ws://localhost:8000/ws"
        print(f"   Connecting to {uri}...")
        async with websockets.connect(uri) as ws:
            print("   ✓ Connected!")
            await ws.send(json.dumps({"command": "version"}))
            response = await ws.recv()
            print(f"   Response: {response}")
            return True
    
    if asyncio.run(test()):
        print("\n✓✓✓ WEBSOCKET BRIDGE IS WORKING! ✓✓✓")
    
except ImportError:
    print("   websockets not installed on host, skipping connection test")
    print("   Install with: pip install websockets")
except Exception as e:
    print(f"   ✗ Connection failed: {e}")

print("\n" + "=" * 70)
print("Test complete")
print("=" * 70)
