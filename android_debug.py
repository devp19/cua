#!/usr/bin/env python3
"""
Android Debug Script - Diagnose WebSocket connection issues
"""

import asyncio
import subprocess
import time

async def main():
    container_name = "android-debug-test"
    
    print("=" * 70)
    print("ANDROID WEBSOCKET DEBUG TOOL")
    print("=" * 70)
    
    # Step 1: Check if container exists
    print("\n1. Checking for existing container...")
    check_cmd = ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    
    if container_name in result.stdout:
        print(f"   Found existing container: {container_name}")
        print("   Removing it...")
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
    
    # Step 2: Start container
    print("\n2. Starting Android container...")
    cmd = [
        "docker", "run", "-d", "--privileged",
        "--name", container_name,
        "-p", "6080:6080",  # VNC
        "-p", "8000:8000",  # API
        "-e", "EMULATOR_DEVICE=Samsung Galaxy S10",
        "-e", "WEB_VNC=true",
        "budtmo/docker-android:emulator_11.0"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ❌ Failed to start container: {result.stderr}")
        return
    
    print(f"   ✅ Container started: {result.stdout.strip()[:12]}")
    print("   View at: http://localhost:6080")
    
    # Step 3: Wait for ADB
    print("\n3. Waiting for ADB to be ready...")
    for i in range(30):
        cmd = ["docker", "exec", container_name, "adb", "devices"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and "device" in result.stdout:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                print(f"   ✅ ADB ready: {result.stdout.strip()}")
                break
        
        if i % 5 == 0:
            print(f"   Waiting... ({i}s)")
        await asyncio.sleep(2)
    
    # Step 4: Check Python and pip
    print("\n4. Checking Python environment in container...")
    
    # Check Python
    cmd = ["docker", "exec", container_name, "python3", "--version"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✅ Python: {result.stdout.strip()}")
    else:
        print(f"   ❌ Python3 not found: {result.stderr}")
    
    # Check pip
    cmd = ["docker", "exec", container_name, "pip3", "--version"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✅ pip3: {result.stdout.strip()}")
    else:
        print(f"   ⚠️  pip3 not found, trying pip...")
        cmd = ["docker", "exec", container_name, "pip", "--version"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ pip: {result.stdout.strip()}")
        else:
            print(f"   ❌ No pip found: {result.stderr}")
    
    # Step 5: Install websockets
    print("\n5. Installing websockets module...")
    cmd = ["docker", "exec", container_name, "pip3", "install", "websockets"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✅ websockets installed")
    else:
        print(f"   ❌ Failed to install: {result.stderr}")
        print("   Trying with pip...")
        cmd = ["docker", "exec", container_name, "pip", "install", "websockets"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ websockets installed with pip")
        else:
            print(f"   ❌ Failed: {result.stderr}")
    
    # Step 6: Copy bridge script
    print("\n6. Copying android_bridge.py to container...")
    import os
    bridge_path = os.path.join(os.path.dirname(__file__), 
                               "libs/python/computer/computer/providers/androiddocker/android_bridge.py")
    
    if not os.path.exists(bridge_path):
        print(f"   ❌ Bridge script not found at: {bridge_path}")
        return
    
    cmd = ["docker", "cp", bridge_path, f"{container_name}:/tmp/computer_server.py"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✅ Bridge script copied")
    else:
        print(f"   ❌ Failed to copy: {result.stderr}")
        return
    
    # Step 7: Start bridge server
    print("\n7. Starting WebSocket bridge server...")
    cmd = ["docker", "exec", "-d", container_name, "python3", "/tmp/computer_server.py", container_name]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✅ Server started")
    else:
        print(f"   ❌ Failed to start: {result.stderr}")
    
    # Wait for server to start
    await asyncio.sleep(3)
    
    # Step 8: Check if server is running
    print("\n8. Verifying server is running...")
    cmd = ["docker", "exec", container_name, "ps", "aux"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if "computer_server.py" in result.stdout:
        print("   ✅ Server process found in ps output")
        # Show the process line
        for line in result.stdout.split('\n'):
            if "computer_server.py" in line:
                print(f"   Process: {line.strip()}")
    else:
        print("   ❌ Server process NOT found")
        print("\n   Checking logs...")
        cmd = ["docker", "exec", container_name, "cat", "/tmp/computer_server.log"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            print(f"   Logs:\n{result.stdout}")
        else:
            print("   No logs found")
    
    # Step 9: Check if port 8000 is listening
    print("\n9. Checking if port 8000 is listening...")
    cmd = ["docker", "exec", container_name, "netstat", "-tlnp"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if ":8000" in result.stdout:
        print("   ✅ Port 8000 is listening")
        for line in result.stdout.split('\n'):
            if ":8000" in line:
                print(f"   {line.strip()}")
    else:
        print("   ❌ Port 8000 NOT listening")
        print(f"   netstat output:\n{result.stdout}")
    
    # Step 10: Try to connect from host
    print("\n10. Testing WebSocket connection from host...")
    try:
        import websockets
        
        async def test_connection():
            try:
                async with websockets.connect("ws://localhost:8000/ws", timeout=5) as ws:
                    # Send a test command
                    await ws.send(json.dumps({"action": "screenshot"}))
                    response = await ws.recv()
                    print(f"   ✅ Connection successful!")
                    print(f"   Response: {response[:100]}...")
                    return True
            except Exception as e:
                print(f"   ❌ Connection failed: {e}")
                return False
        
        import json
        success = await test_connection()
        
    except ImportError:
        print("   ⚠️  websockets module not installed on host")
        print("   Install with: pip install websockets")
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print(f"\nContainer: {container_name}")
    print("VNC: http://localhost:6080")
    print("API: ws://localhost:8000/ws")
    print("\nTo view logs:")
    print(f"  docker exec {container_name} cat /tmp/computer_server.log")
    print("\nTo stop container:")
    print(f"  docker rm -f {container_name}")

if __name__ == "__main__":
    asyncio.run(main())
