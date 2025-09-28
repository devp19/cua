#!/usr/bin/env python3
"""
Test script for Android Docker Provider
Tests the implementation step by step with detailed logging.
"""

import asyncio
import logging
import sys
import subprocess
from pathlib import Path

# Add the computer SDK to path
sys.path.insert(0, str(Path(__file__).parent / "libs" / "python" / "computer"))

from computer.computer import Computer
from computer.providers.base import VMProviderType
from computer.logger import LogLevel

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_prerequisites():
    """Check if Docker and the Android image are available."""
    print("\n" + "="*60)
    print("CHECKING PREREQUISITES")
    print("="*60)
    
    # Check Docker
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker installed: {result.stdout.strip()}")
        else:
            print("❌ Docker not found or not running")
            return False
    except FileNotFoundError:
        print("❌ Docker command not found")
        return False
    
    # Check if Docker daemon is running
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker daemon is running")
        else:
            print("❌ Docker daemon is not running. Please start Docker.")
            return False
    except:
        print("❌ Cannot connect to Docker daemon")
        return False
    
    # Check for Android image
    result = subprocess.run(
        ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
        capture_output=True, text=True
    )
    if "budtmo/docker-android" in result.stdout:
        print("✅ Android Docker image found")
    else:
        print("⚠️  Android image not found. Will pull when starting...")
        print("   Run: docker pull budtmo/docker-android:emulator_11.0")
    
    # Check ADB (optional, for debugging)
    try:
        result = subprocess.run(["adb", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ADB installed: {result.stdout.split('\\n')[0]}")
        else:
            print("⚠️  ADB not found (optional, only needed for debugging)")
    except FileNotFoundError:
        print("⚠️  ADB not found (optional, only needed for debugging)")
    
    print("="*60 + "\n")
    return True


async def test_basic_functionality():
    """Test basic Android provider functionality."""
    print("\n" + "="*60)
    print("TESTING ANDROID DOCKER PROVIDER")
    print("="*60)
    
    computer = None
    try:
        # Step 1: Create Computer instance
        print("\n1. Creating Computer instance with Android provider...")
        computer = Computer(
            display="1280x720",
            memory="4GB",
            cpu="4",
            os_type="linux",  # Android container runs Linux
            provider_type=VMProviderType.ANDROID,
            name="android-test-container",
            verbosity=LogLevel.DEBUG,
            ephemeral=True,
            port=8000
        )
        print("   ✅ Computer instance created")
        
        # Step 2: Start the container
        print("\n2. Starting Android container (this may take 1-2 minutes)...")
        await computer.run()
        print("   ✅ Container started and API server ready")
        
        # Wait for everything to stabilize
        print("\n3. Waiting for Android emulator to fully boot...")
        await asyncio.sleep(10)
        
        # Step 3: Test screenshot
        print("\n4. Testing screenshot capture...")
        try:
            screenshot = await computer.interface.screenshot()
            if screenshot and len(screenshot) > 0:
                # Save screenshot
                with open("test_screenshot.png", "wb") as f:
                    f.write(screenshot)
                print(f"   ✅ Screenshot captured ({len(screenshot)} bytes)")
                print(f"   📸 Saved to: test_screenshot.png")
            else:
                print("   ❌ Screenshot failed - no data returned")
        except Exception as e:
            print(f"   ❌ Screenshot failed: {e}")
        
        # Step 4: Test click
        print("\n5. Testing click/tap at center of screen...")
        try:
            await computer.interface.left_click(640, 360)
            print("   ✅ Click executed")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"   ❌ Click failed: {e}")
        
        # Step 5: Test typing
        print("\n6. Testing text input...")
        try:
            await computer.interface.type_text("Hello Android!")
            print("   ✅ Text typed")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"   ❌ Type text failed: {e}")
        
        # Step 6: Test swipe/scroll
        print("\n7. Testing swipe/scroll...")
        try:
            await computer.interface.drag(640, 600, 640, 200, duration=300)
            print("   ✅ Swipe executed")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"   ❌ Swipe failed: {e}")
        
        # Step 7: Test Android-specific features (if provider has them)
        print("\n8. Testing Android-specific features...")
        provider = computer._vm_provider
        
        if hasattr(provider, 'home'):
            try:
                await provider.home()
                print("   ✅ Home button pressed")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"   ❌ Home button failed: {e}")
        
        if hasattr(provider, 'open_url'):
            try:
                print("   Opening Google.com...")
                await provider.open_url("https://www.google.com")
                print("   ✅ URL opened")
                await asyncio.sleep(5)
                
                # Take screenshot of browser
                screenshot = await computer.interface.screenshot()
                if screenshot:
                    with open("test_browser.png", "wb") as f:
                        f.write(screenshot)
                    print("   📸 Browser screenshot saved to: test_browser.png")
            except Exception as e:
                print(f"   ❌ Open URL failed: {e}")
        
        print("\n" + "="*60)
        print("✅ BASIC TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if computer:
            print("\n9. Cleaning up...")
            try:
                await computer.stop()
                print("   ✅ Container stopped")
            except Exception as e:
                print(f"   ⚠️  Error stopping container: {e}")


async def test_advanced_features():
    """Test more advanced Android features."""
    print("\n" + "="*60)
    print("ADVANCED ANDROID TESTS")
    print("="*60)
    
    computer = Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-advanced-test",
        verbosity=LogLevel.INFO,
        ephemeral=True
    )
    
    try:
        await computer.run()
        await asyncio.sleep(10)
        
        provider = computer._vm_provider
        
        # Test app operations
        print("\n1. Testing app operations...")
        
        # Open Settings
        if hasattr(provider, 'open_app'):
            try:
                await provider.open_app("com.android.settings")
                print("   ✅ Settings app opened")
                await asyncio.sleep(3)
            except Exception as e:
                print(f"   ❌ Failed to open Settings: {e}")
        
        # Navigate back
        if hasattr(provider, 'back'):
            try:
                await provider.back()
                print("   ✅ Back button pressed")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"   ❌ Back button failed: {e}")
        
        print("\n✅ Advanced tests completed")
        
    finally:
        await computer.stop()


async def test_websocket_connection():
    """Test the WebSocket connection directly."""
    print("\n" + "="*60)
    print("TESTING WEBSOCKET CONNECTION")
    print("="*60)
    
    computer = Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-ws-test",
        verbosity=LogLevel.DEBUG,
        ephemeral=True
    )
    
    try:
        await computer.run()
        
        # The interface should be connected via WebSocket
        if computer.interface:
            print("✅ WebSocket interface connected")
            
            # Test a simple operation through WebSocket
            screenshot = await computer.interface.screenshot()
            if screenshot:
                print(f"✅ WebSocket communication working ({len(screenshot)} bytes received)")
            else:
                print("❌ WebSocket communication failed")
        else:
            print("❌ No interface available")
            
    finally:
        await computer.stop()


async def main():
    """Main test runner."""
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install Docker and ensure it's running.")
        return 1
    
    # Run tests
    try:
        # Basic functionality test
        await test_basic_functionality()
        
        # Ask user if they want to run advanced tests
        print("\n" + "="*60)
        response = input("Run advanced tests? (y/n): ").lower()
        if response == 'y':
            await test_advanced_features()
        
        # Ask user if they want to test WebSocket
        response = input("Test WebSocket connection? (y/n): ").lower()
        if response == 'y':
            await test_websocket_connection()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS COMPLETED")
        print("="*60)
        print("\nCheck the following files:")
        print("  - test_screenshot.png - Initial Android screen")
        print("  - test_browser.png - Browser with Google.com")
        print("\nYou can also check the Web VNC interface at:")
        print("  http://localhost:6080")
        print("="*60)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
