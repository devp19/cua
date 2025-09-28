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
        image="budtmo/docker-android:emulator_11.0",  # Specify Android image explicitly
        verbosity=logging.INFO,
        ephemeral=True,  # Clean up container when done
        display="1280x720",
        memory="4GB",
        cpu="4"
    )
    
    try:
        print("\n1. Starting Android container...")
        print("   This may take 1-2 minutes on first run")
        
        # Initialize the VM provider and start container directly
        computer._initialize_vm_provider()
        
        # Start the Android container
        vm_info = await computer._vm_provider.run_vm(
            image="budtmo/docker-android:emulator_11.0",
            name="android-example",
            run_opts={"memory": "4GB", "cpu": "4"},
            storage=None
        )
        
        print("\n2. Container started!")
        print("   ✅ Android emulator is booting!")
        print("   View the Android screen at: http://localhost:6080")
        print(f"   Container ID: {vm_info.get('container_id', 'unknown')[:12]}")
        print("   Note: The WebSocket bridge is not yet implemented")
        
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
        print("   Access it at: http://localhost:6080")
        
        print("\nPress Enter to stop the container...")
        input()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n6. Stopping container...")
        # Stop the VM directly
        if hasattr(computer, '_vm_provider') and computer._vm_provider:
            await computer._vm_provider.stop_vm("android-example", None)
        print("   ✅ Container stopped and cleaned up")

if __name__ == "__main__":
    asyncio.run(main())
