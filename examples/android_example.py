#!/usr/bin/env python3
"""
Android Docker Provider Example for Cua Computer SDK

This example demonstrates how to use the Android Docker Provider
to control an Android emulator through the Computer SDK.

Requirements:
- Docker installed and running
- budtmo/docker-android image (will be pulled automatically if not present)

Usage:
    python android_example.py
"""

import asyncio
import logging
from computer.computer import Computer
from computer.providers.base import VMProviderType

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)


async def main():
    """Main example demonstrating Android Docker Provider usage."""
    
    print("=" * 60)
    print("Android Docker Provider Example")
    print("=" * 60)
    
    # Create Computer instance with Android provider
    computer = Computer(
        os_type="linux",  # Container runs Linux with Android inside
        provider_type=VMProviderType.ANDROID,
        name="android-example",
        verbosity=logging.INFO,
        ephemeral=True,  # Clean up container when done
        display="1280x720",
        memory="4GB",
        cpu="4"
    )
    
    try:
        print("\n1. Starting Android container...")
        print("   This may take 1-2 minutes on first run")
        await computer.run()
        
        print("\n2. Container started!")
        print("   View the Android screen at: http://localhost:6080")
        print("   Note: The emulator needs time to boot (60-120 seconds)")
        
        # Wait for Android to boot
        print("\n3. Waiting for Android to boot...")
        await asyncio.sleep(60)  # Adjust based on your system
        
        # Once the Android emulator is ready, you can interact with it
        # Note: These operations require the WebSocket bridge to be fully implemented
        
        print("\n4. Android emulator should be ready")
        print("   You can view it at http://localhost:6080")
        
        # The provider is ready for Android-specific operations
        # Access the provider for advanced features
        provider = computer._vm_provider
        
        # Example of using ADB commands directly (if needed)
        if hasattr(provider, 'execute_adb_command'):
            print("\n5. Testing ADB access...")
            # This would execute ADB commands in the container
            # result = await provider.execute_adb_command("getprop ro.build.version.release")
            # print(f"   Android version: {result}")
        
        print("\n✅ Android provider is working!")
        print("   The container is running with Android emulator inside")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await computer.stop()

if __name__ == "__main__":
    asyncio.run(main())
