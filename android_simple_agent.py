#!/usr/bin/env python3
"""
Simple Android Agent - Direct ADB Integration
No WebSocket, no complexity - just natural language → ADB commands.
"""

import asyncio
import logging
import os
import json
from computer import Computer
from computer.providers.base import VMProviderType

# Simple LLM client
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("⚠️  anthropic package not installed. Install with: pip install anthropic")

async def main():
    """Run Android with simple AI control."""
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set!")
        print("\nPlease set your API key:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        return
    
    if not HAS_ANTHROPIC:
        print("❌ ERROR: anthropic package not installed")
        print("Install with: pip install anthropic")
        return
    
    print("=" * 70)
    print("SIMPLE ANDROID AGENT - NATURAL LANGUAGE CONTROL")
    print("=" * 70)
    print(f"\n✅ Anthropic API key found")
    
    # Create Android computer instance
    print("\n📦 Step 1: Starting Android container...")
    print("   This will take 60-120 seconds for the emulator to boot")
    print("   View progress at: http://localhost:6080")
    
    computer = Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-simple-agent",
        image="budtmo/docker-android:emulator_11.0",
        verbosity=logging.WARNING,  # Reduce noise
        ephemeral=True,
        display="1280x720",
        memory="4GB",
        cpu="4"
    )
    
    try:
        # Start container (ignore WebSocket errors)
        try:
            await computer.run()
        except TimeoutError:
            pass  # Expected - WebSocket won't connect
        
        # Get direct provider access
        provider = computer.config.vm_provider
        if not provider:
            print("❌ Could not access provider")
            return
        
        print("\n✅ Container started!")
        print("   Waiting for Android emulator to boot (90 seconds)...")
        await asyncio.sleep(90)
        
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)
        
        print("\n✅ AI Agent ready!")
        print("\n" + "=" * 70)
        print("INTERACTIVE MODE - Natural Language Commands")
        print("=" * 70)
        print("\nExample commands:")
        print("  - 'Open the Settings app'")
        print("  - 'Go to the home screen'")
        print("  - 'Tap in the center of the screen'")
        print("  - 'Go to home screen'")
        print("  - 'Open website devp.ca'")
        print("  - 'exit' to quit")
        print("\n" + "=" * 70)
        
        # Conversation history
        conversation = []
        
        # Interactive loop
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Exiting...")
                    break
                
                print(f"\n🤖 Processing: '{user_input}'")
                
                # Take screenshot for vision
                print("   📸 Taking screenshot...")
                screenshot_bytes = await provider.screenshot()
                
                if screenshot_bytes:
                    import base64
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                    
                    # Add user message with image
                    conversation.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64
                                }
                            },
                            {
                                "type": "text",
                                "text": user_input
                            }
                        ]
                    })
                else:
                    # Fallback without image
                    conversation.append({
                        "role": "user",
                        "content": user_input
                    })
                
                # Call Claude to get ADB commands
                system_prompt = """You are an Android automation assistant. Convert user requests into ADB commands.

You can SEE the Android screen in the image provided. Analyze what's visible and determine the correct actions.

Available ADB functions (call these directly):
- home() - Go to home screen
- back() - Press back button
- recents() - Show recent apps
- open_app(package) - Open app by package name (e.g., "com.android.settings")
- open_url(url) - Open URL in browser
- tap(x, y) - Tap at coordinates (screen is 1280x720)
- swipe(x1, y1, x2, y2, duration) - Swipe gesture
- type_text(text) - Type text
- key_event(keycode) - Send key event (66=Enter, 67=Backspace)

IMPORTANT: Look at the image to find UI elements. If user says "tap the 3 dots top right", look at the image, find the 3 dots icon, estimate its coordinates, and tap there.

Common package names:
- Settings: com.android.settings
- Chrome: com.android.chrome
- Calculator: com.android.calculator2

Respond with a JSON array of commands to execute. Example:
[
  {"function": "home"},
  {"function": "open_app", "args": {"package": "com.android.settings"}},
  {"function": "tap", "args": {"x": 640, "y": 360}}
]

Only return the JSON array, nothing else."""

                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=system_prompt,
                    messages=conversation
                )
                
                # Extract commands from response
                response_text = response.content[0].text.strip()
                
                # Add assistant response to conversation
                conversation.append({
                    "role": "assistant",
                    "content": response_text
                })
                
                print(f"\n💬 Agent: {response_text}\n")
                
                # Parse and execute commands
                try:
                    # Extract JSON from response (handle markdown code blocks)
                    if "```json" in response_text:
                        json_str = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        json_str = response_text.split("```")[1].split("```")[0].strip()
                    else:
                        json_str = response_text
                    
                    commands = json.loads(json_str)
                    
                    if not isinstance(commands, list):
                        commands = [commands]
                    
                    # Execute each command
                    for cmd in commands:
                        func_name = cmd.get("function")
                        args = cmd.get("args", {})
                        
                        print(f"   Executing: {func_name}({args})")
                        
                        # Call the provider method
                        if func_name == "home":
                            await provider.home()
                        elif func_name == "back":
                            await provider.back()
                        elif func_name == "recents":
                            await provider.recents()
                        elif func_name == "open_app":
                            await provider.open_app(args["package"])
                        elif func_name == "open_url":
                            await provider.open_url(args["url"])
                        elif func_name == "tap":
                            await provider.tap(args["x"], args["y"])
                        elif func_name == "swipe":
                            await provider.swipe(
                                args["x1"], args["y1"],
                                args["x2"], args["y2"],
                                args.get("duration", 300)
                            )
                        elif func_name == "type_text":
                            await provider.type_text(args["text"])
                        elif func_name == "key_event":
                            await provider.key_event(args["keycode"])
                        else:
                            print(f"   ⚠️  Unknown function: {func_name}")
                        
                        await asyncio.sleep(0.5)  # Small delay between commands
                    
                    print("\n✅ Commands executed!")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse commands: {e}")
                    print(f"   Response was: {response_text}")
                
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
            import subprocess
            subprocess.run(["docker", "stop", "android-simple-agent"], capture_output=True)
            subprocess.run(["docker", "rm", "android-simple-agent"], capture_output=True)
        print("✅ Container stopped and cleaned up")


if __name__ == "__main__":
    asyncio.run(main())
