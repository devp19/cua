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
        print(f"   Status: {vm_info}")
        
        # Test 3: Test ADB directly
        print("\n3. Testing ADB in container...")
        cmd = ["docker", "exec", "android-direct-test", "adb", "devices"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ ADB output:\n{result.stdout}")
        else:
            print(f"   ❌ ADB failed: {result.stderr}")
        
        # Test 4: Take screenshot using ADB
        print("\n4. Taking screenshot with ADB...")
        cmd = ["docker", "exec", "android-direct-test", "adb", "shell", "screencap", "-p"]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0 and len(result.stdout) > 0:
            with open("android_direct_screenshot.png", "wb") as f:
                f.write(result.stdout)
            print(f"   ✅ Screenshot saved ({len(result.stdout)} bytes)")
        else:
            print("   ❌ Screenshot failed")
        
        # Test 5: Check Web VNC
        print("\n5. Web VNC available at:")
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
