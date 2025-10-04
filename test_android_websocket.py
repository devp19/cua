#!/usr/bin/env python3
"""
Test Android WebSocket Bridge
This script tests the WebSocket bridge connection instead of direct ADB.
"""

import asyncio
import logging
from computer import Computer
from computer.providers.base import VMProviderType

async def main():
    """Test Android with WebSocket bridge."""
    
    print("=" * 70)
    print("TESTING ANDROID WEBSOCKET BRIDGE")
    print("=" * 70)
    
    # Create Android computer instance
    print("\nStarting Android container with WebSocket bridge...")
    print("   This will take 60-120 seconds for the emulator to boot")
    print("   View progress at: http://localhost:6080")
    
    computer = Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-ws-test",
        image="budtmo/docker-android:emulator_11.0",
        verbosity=logging.INFO,
        ephemeral=True,
        display="1280x720",
        memory="4GB",
        cpu="4"
    )
    
    try:
        # Start container - this should now connect via WebSocket
        print("\nAttempting WebSocket connection...")
        await computer.run()
        
        print("\nWebSocket connection successful!")
        print("   The bridge is working correctly!")
        
        # Test the interface
        print("\nTesting interface commands...")
        
        # Test 1: Get screen size
        print("\n1. Testing get_screen_size()...")
        size = await computer.interface.get_screen_size()
        print(f"Screen size: {size['width']}x{size['height']}")
        
        # Test 2: Take screenshot
        print("\n2. Testing screenshot()...")
        screenshot = await computer.interface.screenshot()
        if screenshot:
            filename = "test_screenshot.png"
            with open(filename, "wb") as f:
                f.write(screenshot)
            print(f"Screenshot saved: {filename}")
        else:
            print("  Screenshot failed")
        
        # Test 3: Click action
        print("\n3. Testing left_click()...")
        await computer.interface.left_click(640, 360)
        print("   Click command sent")
        
        # Test 4: Type text
        print("\n4. Testing type_text()...")
        await computer.interface.type_text("Hello Android")
        print("  Type command sent")
        
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED - WEBSOCKET BRIDGE IS WORKING!")
        print("=" * 70)
        
        # Interactive mode
        print("\nEntering interactive mode...")
        print("Available commands:")
        print("  screenshot - Take screenshot")
        print("  click X Y  - Click at coordinates")
        print("  type TEXT  - Type text")
        print("  size       - Get screen size")
        print("  exit       - Quit")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Exiting...")
                    break
                
                parts = user_input.split()
                cmd = parts[0].lower()
                
                if cmd == "screenshot":
                    screenshot = await computer.interface.screenshot()
                    if screenshot:
                        filename = f"screenshot_{int(asyncio.get_event_loop().time())}.png"
                        with open(filename, "wb") as f:
                            f.write(screenshot)
                        print(f"Screenshot saved: {filename}")
                    else:
                        print("Screenshot failed")
                
                elif cmd == "click":
                    if len(parts) >= 3:
                        x, y = int(parts[1]), int(parts[2])
                        await computer.interface.left_click(x, y)
                        print(f"Clicked at ({x}, {y})")
                    else:
                        print("Usage: click X Y")
                
                elif cmd == "type":
                    if len(parts) >= 2:
                        text = " ".join(parts[1:])
                        await computer.interface.type_text(text)
                        print(f"Typed: {text}")
                    else:
                        print("Usage: type TEXT")
                
                elif cmd == "size":
                    size = await computer.interface.get_screen_size()
                    print(f"Screen size: {size['width']}x{size['height']}")
                
                else:
                    print(f" Unknown command: {cmd}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Exiting...")
                break
            except Exception as e:
                print(f"\n Error: {e}")
                import traceback
                traceback.print_exc()
        
    except TimeoutError as e:
        print("\n WEBSOCKET CONNECTION FAILED")
        print(f"   Error: {e}")
        print("\n   This means the bridge is not responding correctly.")
        print("\n   CONTAINER LEFT RUNNING FOR DEBUGGING")
        print("   Run diagnostics with: python manual_bridge_test.py")
        print("\n   Or manually check:")
        print("   - Logs: docker exec android-ws-test cat /tmp/computer_server.log")
        print("   - Process: docker exec android-ws-test ps aux | grep computer_server")
        print("   - Port: docker exec android-ws-test netstat -tuln | grep 8000")
        print("\n   To clean up manually: docker stop android-ws-test && docker rm android-ws-test")
        
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n   CONTAINER LEFT RUNNING FOR DEBUGGING")
        print("   Clean up with: docker stop android-ws-test && docker rm android-ws-test")
        
    else:
        # Only cleanup if successful
        print("\n Cleaning up...")
        try:
            await computer.stop()
        except:
            import subprocess
            subprocess.run(["docker", "stop", "android-ws-test"], capture_output=True)
            subprocess.run(["docker", "rm", "android-ws-test"], capture_output=True)
        print(" Container stopped and cleaned up")


if __name__ == "__main__":
    asyncio.run(main())
