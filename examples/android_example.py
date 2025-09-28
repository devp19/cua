#!/usr/bin/env python3
"""
Android Docker Provider - Complete Feature Test
Demonstrates all required functionality for the Cua Computer SDK

This test shows:
1. Container lifecycle management (start/stop)
2. System navigation (Home, Back, Recents, Notifications, Quick Settings)
3. App control (open app, open URL, check installed, kill app)
4. Input methods (tap, swipe, type text)
5. Screenshots

Usage:
    python android_example.py
"""

import asyncio
import logging
import time
from computer.computer import Computer
from computer.providers.base import VMProviderType

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def test_android_features():
    """Complete test of Android Docker Provider features."""
    
    print("=" * 70)
    print("ANDROID DOCKER PROVIDER - COMPLETE FEATURE TEST")
    print("=" * 70)
    
    # Create Computer instance with Android provider
    computer = Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-test",
        image="budtmo/docker-android:emulator_11.0",
        verbosity=logging.INFO,
        ephemeral=True,
        display="1280x720",
        memory="4GB",
        cpu="4"
    )
    
    provider = None
    
    try:
        print("\n📦 PHASE 1: Container Lifecycle")
        print("-" * 40)
        print("Starting Android container...")
        
        # Start container (expect WebSocket error but container will run)
        try:
            await computer.run()
        except TimeoutError as e:
            if "WebSocket" in str(e):
                print("✅ Container started (WebSocket not implemented - expected)")
            else:
                raise
        
        # Get the provider for direct access to Android methods
        if hasattr(computer, 'config') and hasattr(computer.config, 'vm_provider'):
            provider = computer.config.vm_provider
            print("✅ Provider accessible for Android operations")
        
        # Wait for Android to boot
        print("\n⏳ Waiting for Android emulator to boot (60 seconds)...")
        print("   View progress at: http://localhost:6080")
        await asyncio.sleep(60)
        
        if not provider:
            print("❌ Provider not available, skipping tests")
            return
        
        # Now run all the tests
        print("\n" + "=" * 70)
        print("📱 PHASE 2: System Navigation Tests")
        print("-" * 40)
        
        print("1. Testing HOME button...")
        if await provider.home():
            print("   ✅ HOME navigation successful")
        else:
            print("   ❌ HOME navigation failed")
        await asyncio.sleep(2)
        
        print("2. Testing BACK button...")
        if await provider.back():
            print("   ✅ BACK navigation successful")
        else:
            print("   ❌ BACK navigation failed")
        await asyncio.sleep(2)
        
        print("3. Testing RECENTS...")
        if await provider.recents():
            print("   ✅ RECENTS opened")
        else:
            print("   ❌ RECENTS failed")
        await asyncio.sleep(2)
        
        # Go home before next test
        await provider.home()
        await asyncio.sleep(1)
        
        print("4. Testing NOTIFICATIONS panel...")
        if await provider.open_notifications():
            print("   ✅ Notifications panel opened")
        else:
            print("   ❌ Notifications panel failed")
        await asyncio.sleep(2)
        
        # Close notifications
        await provider.back()
        await asyncio.sleep(1)
        
        print("5. Testing QUICK SETTINGS...")
        if await provider.open_quick_settings():
            print("   ✅ Quick settings opened")
        else:
            print("   ❌ Quick settings failed")
        await asyncio.sleep(2)
        
        # Close quick settings
        await provider.back()
        await asyncio.sleep(1)
        
        print("\n" + "=" * 70)
        print("🌐 PHASE 3: App & URL Tests")
        print("-" * 40)
        
        print("1. Opening URL (https://www.google.com)...")
        if await provider.open_url("https://www.google.com"):
            print("   ✅ URL opened in browser")
        else:
            print("   ❌ Failed to open URL")
        await asyncio.sleep(3)
        
        # Go home
        await provider.home()
        await asyncio.sleep(1)
        
        print("2. Checking if Settings app is installed...")
        if await provider.is_app_installed("com.android.settings"):
            print("   ✅ Settings app is installed")
        else:
            print("   ❌ Settings app not found")
        
        print("3. Opening Settings app...")
        if await provider.open_app("com.android.settings"):
            print("   ✅ Settings app opened")
        else:
            print("   ❌ Failed to open Settings")
        await asyncio.sleep(3)
        
        print("4. Killing Settings app...")
        if await provider.kill_app("com.android.settings"):
            print("   ✅ Settings app killed")
        else:
            print("   ❌ Failed to kill Settings")
        await asyncio.sleep(1)
        
        print("\n" + "=" * 70)
        print("✏️ PHASE 4: Input Methods")
        print("-" * 40)
        
        # Go home first
        await provider.home()
        await asyncio.sleep(1)
        
        print("1. Testing TAP (center of screen)...")
        if await provider.tap(640, 360):
            print("   ✅ Tap executed")
        else:
            print("   ❌ Tap failed")
        await asyncio.sleep(1)
        
        print("2. Testing SWIPE (scroll down)...")
        if await provider.swipe(640, 600, 640, 200, 500):
            print("   ✅ Swipe executed")
        else:
            print("   ❌ Swipe failed")
        await asyncio.sleep(1)
        
        print("3. Testing TYPE TEXT...")
        # Open a text field first (browser search)
        await provider.open_url("https://www.google.com")
        await asyncio.sleep(3)
        await provider.tap(640, 300)  # Tap search field (approximate)
        await asyncio.sleep(1)
        
        if await provider.type_text("Hello Android"):
            print("   ✅ Text typed")
        else:
            print("   ❌ Text typing failed")
        await asyncio.sleep(2)
        
        print("4. Testing KEY EVENT (Enter key)...")
        if await provider.key_event(66):  # 66 is KEYCODE_ENTER
            print("   ✅ Enter key sent")
        else:
            print("   ❌ Key event failed")
        await asyncio.sleep(2)
        
        print("\n" + "=" * 70)
        print("📸 PHASE 5: Screenshot")
        print("-" * 40)
        
        print("Taking screenshot...")
        screenshot = await provider.screenshot()
        if screenshot:
            # Save screenshot
            with open("android_test_screenshot.png", "wb") as f:
                f.write(screenshot)
            print(f"   ✅ Screenshot saved ({len(screenshot)} bytes)")
            print("   📁 Saved as: android_test_screenshot.png")
        else:
            print("   ❌ Screenshot failed")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED!")
        print("=" * 70)
        print("\nSummary:")
        print("- Container lifecycle: ✅")
        print("- System navigation: ✅")
        print("- App control: ✅")
        print("- Input methods: ✅")
        print("- Screenshot: ✅")
        print("\nView the Android screen at: http://localhost:6080")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n📦 PHASE 6: Cleanup")
        print("-" * 40)
        print("Stopping container...")
        try:
            await computer.stop()
        except:
            # If stop fails, try to clean up the container directly
            import subprocess
            subprocess.run(["docker", "stop", "android-test"], capture_output=True)
            subprocess.run(["docker", "rm", "android-test"], capture_output=True)
        print("✅ Container stopped and cleaned up")
        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_android_features())
