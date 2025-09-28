#!/usr/bin/env python3
"""
Quick test for Android Docker Provider
Minimal test to verify the provider works.
"""

import asyncio
import sys
from pathlib import Path

# Add the computer SDK to path
sys.path.insert(0, str(Path(__file__).parent / "libs" / "python" / "computer"))

from computer.computer import Computer
from computer.providers.base import VMProviderType
from computer.logger import LogLevel


async def quick_test():
    """Quick test of Android provider."""
    print("\n🚀 Quick Android Provider Test\n" + "="*40)
    
    computer = Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-quick-test",
        verbosity=LogLevel.INFO,
        ephemeral=True
    )
    
    try:
        print("1. Starting Android container...")
        await computer.run()
        
        print("2. Waiting for boot (10 seconds)...")
        await asyncio.sleep(10)
        
        print("3. Taking screenshot...")
        screenshot = await computer.interface.screenshot()
        
        if screenshot:
            with open("android_test.png", "wb") as f:
                f.write(screenshot)
            print(f"✅ Success! Screenshot saved to android_test.png")
            print(f"   Size: {len(screenshot)} bytes")
        else:
            print("❌ Failed to capture screenshot")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("4. Stopping container...")
        await computer.stop()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(quick_test())
