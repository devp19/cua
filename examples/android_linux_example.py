#!/usr/bin/env python3
"""
Android Docker Provider Example - Using Linux OS Type
This demonstrates that the Android emulator runs in a Linux container,
so we can use os_type="linux" with the Android provider.
"""

import asyncio
import logging
from computer.computer import Computer
from computer.providers.base import VMProviderType
from computer.logger import LogLevel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main example using Linux OS type with Android provider."""
    
    # Create Computer instance with Linux OS and Android provider
    # This works because the Android emulator runs inside a Linux container
    computer = Computer(
        display="1280x720",
        memory="4GB",
        cpu="4",
        os_type="linux",  # The container runs Linux!
        provider_type=VMProviderType.ANDROID,  # But we use the Android provider
        name="android-linux-test",
        verbosity=LogLevel.INFO,
        ephemeral=True,
        port=8000
    )
    
    try:
        logger.info("Starting Android emulator in Linux container...")
        await computer.run()
        
        # The computer.interface will be a Linux interface
        # but the container has Android emulator with ADB access
        interface = computer.interface
        
        logger.info("Taking screenshot...")
        screenshot = await interface.screenshot()
        if screenshot:
            with open("android_linux_screenshot.png", "wb") as f:
                f.write(screenshot)
            logger.info("Screenshot saved!")
        
        # Standard Computer SDK operations work
        logger.info("Clicking at center of screen...")
        await interface.left_click(640, 360)
        await asyncio.sleep(1)
        
        logger.info("Typing text...")
        await interface.type_text("Hello from Linux container with Android!")
        await asyncio.sleep(1)
        
        # Scrolling (translated to swipe in Android)
        logger.info("Scrolling...")
        await interface.scroll("down", amount=3)
        await asyncio.sleep(1)
        
        logger.info("Example completed successfully!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        logger.info("Stopping container...")
        await computer.stop()


async def direct_adb_example():
    """Example showing direct ADB access through the provider."""
    
    computer = Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-adb-test",
        verbosity=LogLevel.DEBUG,
        ephemeral=True
    )
    
    try:
        await computer.run()
        
        # Access the provider for Android-specific commands
        provider = computer._vm_provider
        
        if hasattr(provider, 'execute_adb_command'):
            logger.info("Executing ADB commands...")
            
            # Get Android version
            version = await provider.execute_adb_command("getprop ro.build.version.release")
            logger.info(f"Android version: {version.strip()}")
            
            # List installed packages
            packages = await provider.execute_adb_command("pm list packages | head -5")
            logger.info(f"Sample packages:\n{packages}")
            
            # Open a URL
            logger.info("Opening Google...")
            await provider.open_url("https://www.google.com")
            await asyncio.sleep(3)
            
            # Take screenshot through interface
            screenshot = await computer.interface.screenshot()
            if screenshot:
                with open("android_browser.png", "wb") as f:
                    f.write(screenshot)
                logger.info("Browser screenshot saved!")
        
        logger.info("ADB example completed!")
        
    finally:
        await computer.stop()


if __name__ == "__main__":
    print("=" * 60)
    print("Android in Linux Container Example")
    print("=" * 60)
    print()
    print("This demonstrates that the Android emulator runs in a")
    print("Linux container, so we can use os_type='linux' with the")
    print("Android provider. The container has:")
    print()
    print("1. Ubuntu Linux as the base OS")
    print("2. Android emulator running inside")
    print("3. ADB for controlling the emulator")
    print("4. Computer-server API bridging to ADB")
    print()
    print("This is simpler than creating a new OS type!")
    print()
    print("Make sure Docker is running.")
    print("Starting in 3 seconds...")
    print("=" * 60)
    
    import time
    time.sleep(3)
    
    # Run the main example
    asyncio.run(main())
    
    # Uncomment to run the ADB example
    # asyncio.run(direct_adb_example())
