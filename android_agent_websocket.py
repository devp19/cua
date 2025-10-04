#!/usr/bin/env python3
"""
Android Agent with WebSocket Bridge - Full AI Control
Uses the Computer SDK interface with natural language commands.
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
    print(" anthropic package not installed. Install with: pip install anthropic")

async def main():
    """Run Android with AI agent via WebSocket."""
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set!")
        print("\nPlease set your API key:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        return
    
    if not HAS_ANTHROPIC:
        print("ERROR: anthropic package not installed")
        print("Install with: pip install anthropic")
        return
    
    print("=" * 70)
    print("ANDROID AI AGENT - WEBSOCKET BRIDGE")
    print("=" * 70)
    print(f"\nAnthropic API key found")
    
    # Create Android computer instance
    print("\nStarting Android container...")
    print("   This will take 60-120 seconds for the emulator to boot")
    print("   View progress at: http://localhost:6080")
    
    computer = Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-agent",
        image="budtmo/docker-android:emulator_11.0",
        verbosity=logging.WARNING,  # Reduce noise
        ephemeral=True,
        display="1280x720",
        memory="4GB",
        cpu="4"
    )
    
    try:
        # Start container and connect via WebSocket
        await computer.run()
        
        print("\n WebSocket connected!")
        print("   Android agent is ready!")
        
        # Get screen size
        screen_size = await computer.interface.get_screen_size()
        screen_width = screen_size["width"]
        screen_height = screen_size["height"]
        print(f"   Screen resolution: {screen_width}x{screen_height}")
        
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)
        
        print("\n" + "=" * 70)
        print("AI AGENT READY - Enter natural language commands")
        print("=" * 70)
        print("\nExamples:")
        print("  - 'open settings'")
        print("  - 'go to home screen'")
        print("  - 'tap the center of the screen'")
        print("  - 'take a screenshot'")
        print("\nType 'exit' to quit\n")
        
        # Conversation history
        conversation = []
        
        # Interactive loop
        while True:
            try:
                user_input = input("> ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\nExiting...")
                    break
                
                print(f"\nProcessing: '{user_input}'")
                
                # Take screenshot for vision
                print("  Taking screenshot...")
                screenshot_bytes = await computer.interface.screenshot()
                
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
                    conversation.append({
                        "role": "user",
                        "content": user_input
                    })
                
                # Call Claude to get commands
                system_prompt = f"""You are an Android automation assistant. You can SEE the Android screen and control it.

Available commands (use Computer SDK interface):
- await computer.interface.get_screen_size() - Get screen dimensions
- await computer.interface.screenshot() - Take screenshot
- await computer.interface.left_click(x, y) - Tap at coordinates (screen is {screen_width}x{screen_height})
- await computer.interface.type_text(text) - Type text
- await computer.interface.press(key) - Press key (Key.ENTER, Key.BACK, Key.HOME)

IMPORTANT: 
1. Look at the screenshot to find UI elements
2. The screen resolution is {screen_width}x{screen_height}
3. Estimate coordinates based on what you see in the image
4. Return Python code that uses the computer.interface methods

For Android-specific actions:
- Home button: Use Key.HOME or tap at bottom center
- Back button: Use Key.BACK
- Settings: Look for settings icon or use app drawer

Respond with ONLY executable Python code using await and computer.interface methods. No explanations, just code."""

                print("  Asking Claude...")
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=system_prompt,
                    messages=conversation
                )
                
                # Extract code from response
                response_text = response.content[0].text.strip()
                
                # Add assistant response to conversation
                conversation.append({
                    "role": "assistant",
                    "content": response_text
                })
                
                print(f"\n  Agent response:\n{response_text}\n")
                
                # Execute the code
                try:
                    # Extract Python code from markdown if present
                    if "```python" in response_text:
                        code = response_text.split("```python")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        code = response_text.split("```")[1].split("```")[0].strip()
                    else:
                        code = response_text
                    
                    print("  Executing commands...")
                    
                    # Execute the code with computer.interface available
                    exec_globals = {
                        "computer": computer,
                        "Key": __import__('computer.interface.models', fromlist=['Key']).Key,
                        "asyncio": asyncio,
                    }
                    
                    # Execute async code
                    exec(f"async def _execute():\n" + "\n".join(f"    {line}" for line in code.split("\n")), exec_globals)
                    await exec_globals["_execute"]()
                    
                    print("   Commands executed successfully!")
                    
                except Exception as e:
                    print(f"   Execution error: {e}")
                    import traceback
                    traceback.print_exc()
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Exiting...")
                break
            except Exception as e:
                print(f"\n Error: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\nCleaning up...")
        try:
            await computer.stop()
        except:
            import subprocess
            subprocess.run(["docker", "stop", "android-agent"], capture_output=True)
            subprocess.run(["docker", "rm", "android-agent"], capture_output=True)
        print("Container stopped and cleaned up")


if __name__ == "__main__":
    asyncio.run(main())
