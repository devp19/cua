#!/usr/bin/env python3
"""
Basic test for Android Docker Provider
Tests container management without WebSocket dependency.
"""

import asyncio
import subprocess
import sys
from pathlib import Path

# Add the computer SDK to path
sys.path.insert(0, str(Path(__file__).parent / "libs" / "python" / "computer"))

from computer.providers.androiddocker import AndroidDockerProvider


async def test_provider_directly():
    """Test the Android provider directly without Computer SDK wrapper."""
    print("\n🔧 Direct Android Provider Test\n" + "="*40)
    
    # Create provider instance
    provider = AndroidDockerProvider(
        port=8000,
        host="localhost",
        image="budtmo/docker-android:emulator_11.0",
        verbose=True,
        ephemeral=True
    )
    
    print(f"Provider type: {provider.provider_type}")
    print(f"Image: {provider.image}")
    print(f"Port: {provider.port}")
    
    try:
        # Test 1: Start container
        print("\n1. Starting Android container...")
        result = await provider.run_vm(
            image=provider.image,
            name="android-direct-test",
            run_opts={"memory": "4GB", "cpu": "4"},
            storage=None
        )
        print(f"   Result: {result}")
        
        if result.get("status") == "error":
            print(f"   ❌ Error: {result.get('error')}")
            return
        
        print("   ✅ Container started")
        
        # Test 2: Check container status
        print("\n2. Checking container status...")
        vm_info = await provider.get_vm("android-direct-test", None)
        print(f"   Status: {vm_info.get('status')}")
        
        # Wait for emulator to boot
        print("\n3. Waiting for Android emulator to boot...")
        print("   This typically takes 60-120 seconds on first boot")
        print("   You can monitor progress at http://localhost:6080")
        
        # Poll ADB until device is ready
        max_wait = 120
        start_time = asyncio.get_event_loop().time()
        device_ready = False
        
        while asyncio.get_event_loop().time() - start_time < max_wait:
            cmd = ["docker", "exec", "android-direct-test", "adb", "devices"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    for line in lines[1:]:
                        if line.strip() and '\t' in line:
                            device, status = line.strip().split('\t')
                            if status == "device":
                                print(f"   ✅ Device ready: {device}")
                                device_ready = True
                                break
                            elif status == "offline":
                                print(f"   ⏳ Device offline, still booting...")
            
            if device_ready:
                break
            
            elapsed = int(asyncio.get_event_loop().time() - start_time)
            if elapsed % 10 == 0:
                print(f"   ⏳ Waiting... ({elapsed}s elapsed)")
            
            await asyncio.sleep(2)
        
        if not device_ready:
            print("   ❌ Device did not become ready in time")
            print("   Check http://localhost:6080 to see the status")
            return
        
        # Wait a bit more for system to stabilize
        print("   Waiting 5 more seconds for system to stabilize...")
        await asyncio.sleep(5)
        
        # Test 3: Test ADB directly
        print("\n4. Testing ADB in container...")
        cmd = ["docker", "exec", "android-direct-test", "adb", "devices"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ ADB output:\n{result.stdout}")
        else:
            print(f"   ❌ ADB failed: {result.stderr}")
        
        # Test 5: Take screenshot using ADB
        print("\n5. Taking screenshot with ADB...")
        cmd = ["docker", "exec", "android-direct-test", "adb", "shell", "screencap", "-p"]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0 and len(result.stdout) > 0:
            with open("android_direct_screenshot.png", "wb") as f:
                f.write(result.stdout)
            print(f"   ✅ Screenshot saved ({len(result.stdout)} bytes)")
        else:
            print("   ❌ Screenshot failed")
        
        # Test 6: Check Web VNC
        print("\n6. Web VNC available at:")
        print(f"   http://localhost:{provider.vnc_port}")
        
        print("\n" + "="*40)
        print("✅ Basic tests completed!")
        print("\nYou can:")
        print("1. View Android screen at http://localhost:6080")
        print("2. Check screenshot at android_direct_screenshot.png")
        print("3. Access container: docker exec -it android-direct-test bash")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n6. Stopping container...")
        try:
            await provider.stop_vm("android-direct-test", None)
            print("   ✅ Container stopped")
        except Exception as e:
            print(f"   ⚠️ Error stopping: {e}")


if __name__ == "__main__":
    asyncio.run(test_provider_directly())
