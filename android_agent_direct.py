#!/usr/bin/env python3
"""
Android Agent - Direct ADB Control (Workaround)
This version bypasses the WebSocket bridge and uses direct ADB commands.

This is a temporary workaround until the WebSocket integration is fixed.
"""

import asyncio
import logging
import os
from computer import Computer
from computer.providers.base import VMProviderType

async def main():
    """Run Android with direct ADB control (no WebSocket)."""
    
    # Check for API key (for future agent integration)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"✅ Anthropic API key found (starts with: {api_key[:10]}...)")
    else:
        print("⚠️  ANTHROPIC_API_KEY not set (needed for AI agent)")
    
    print("=" * 70)
    print("ANDROID DIRECT CONTROL - ADB COMMANDS")
    print("=" * 70)
    print("\nThis version uses direct ADB commands (no AI agent yet)")
    print("WebSocket integration will be added in a future update")
    
    # Create Android computer instance
    print("\n📦 Step 1: Starting Android container...")
    print("   This will take 60-120 seconds for the emulator to boot")
    print("   View progress at: http://localhost:6080")
    
    computer = Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-direct-demo",
        image="budtmo/docker-android:emulator_11.0",
        verbosity=logging.INFO,
        ephemeral=True,
        display="1280x720",
        memory="4GB",
        cpu="4"
    )
    
    try:
        # Start container (will fail at WebSocket connection, but that's OK)
        print("\n⚠️  Note: WebSocket connection will fail - this is expected")
        print("   We'll use direct ADB control instead\n")
        
        try:
            await computer.run()
        except TimeoutError as e:
            if "WebSocket" in str(e):
                print("✅ Container started (WebSocket failed as expected)")
            else:
                raise
        
        # Get direct provider access
        provider = computer.config.vm_provider
        if not provider:
            print("❌ Could not access provider")
            return
        
        print("\n✅ Container is running!")
        print("   Waiting for Android emulator to boot (90 seconds)...")
        await asyncio.sleep(90)
        
        print("\n" + "=" * 70)
        print("INTERACTIVE MODE - Direct ADB Commands")
        print("=" * 70)
        print("\nAvailable commands:")
        print("  home          - Go to home screen")
        print("  back          - Press back button")
        print("  recents       - Show recent apps")
        print("  settings      - Open Settings app")
        print("  chrome        - Open Chrome browser")
        print("  tap X Y       - Tap at coordinates (e.g., tap 640 360)")
        print("  type TEXT     - Type text (e.g., type Hello)")
        print("  swipe         - Swipe down")
        print("  screenshot    - Take screenshot")
        print("  exit          - Quit")
        print("\n" + "=" * 70)
        
        # Interactive loop
        while True:
            try:
                user_input = input("\n> ").strip().lower()
                
                if not user_input:
                    continue
                
                if user_input in ['exit', 'quit', 'q']:
                    print("\n👋 Exiting...")
                    break
                
                # Parse command
                parts = user_input.split()
                cmd = parts[0]
                args = parts[1:]
                
                # Execute command
                if cmd == "home":
                    await provider.home()
                    print("✅ Navigated to home")
                
                elif cmd == "back":
                    await provider.back()
                    print("✅ Pressed back")
                
                elif cmd == "recents":
                    await provider.recents()
                    print("✅ Opened recents")
                
                elif cmd == "settings":
                    await provider.open_app("com.android.settings")
                    print("✅ Opened Settings")
                
                elif cmd == "chrome":
                    await provider.open_url("https://www.google.com")
                    print("✅ Opened Chrome")
                
                elif cmd == "tap":
                    if len(args) >= 2:
                        x, y = int(args[0]), int(args[1])
                        await provider.tap(x, y)
                        print(f"✅ Tapped at ({x}, {y})")
                    else:
                        print("❌ Usage: tap X Y")
                
                elif cmd == "type":
                    if args:
                        text = " ".join(args)
                        await provider.type_text(text)
                        print(f"✅ Typed: {text}")
                    else:
                        print("❌ Usage: type TEXT")
                
                elif cmd == "swipe":
                    await provider.swipe(640, 600, 640, 200, 500)
                    print("✅ Swiped down")
                
                elif cmd == "screenshot":
                    screenshot = await provider.screenshot()
                    if screenshot:
                        filename = f"android_screenshot_{int(asyncio.get_event_loop().time())}.png"
                        with open(filename, "wb") as f:
                            f.write(screenshot)
                        print(f"✅ Screenshot saved: {filename}")
                    else:
                        print("❌ Screenshot failed")
                
                else:
                    print(f"❌ Unknown command: {cmd}")
                    print("   Type 'help' to see available commands")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Exiting...")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 70)
        print("SESSION COMPLETE")
        print("=" * 70)
        
    finally:
        print("\n📦 Cleaning up...")
        try:
            await computer.stop()
        except:
            # If stop fails, try to clean up the container directly
            import subprocess
            subprocess.run(["docker", "stop", "android-direct-demo"], capture_output=True)
            subprocess.run(["docker", "rm", "android-direct-demo"], capture_output=True)
        print("✅ Container stopped and cleaned up")


if __name__ == "__main__":
    asyncio.run(main())
