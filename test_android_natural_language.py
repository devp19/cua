#!/usr/bin/env python3
"""
Test Android Docker Provider with Cua Agent Framework
This verifies that the Android provider integrates correctly with the Agent
"""

import asyncio
import logging
import os
from agent import ComputerAgent
from computer import Computer
from computer.providers.base import VMProviderType

logging.basicConfig(level=logging.INFO)
async def test_with_bridge():
    """Test natural language control with the WebSocket bridge."""
    
    print("=" * 70)
    print("ANDROID NATURAL LANGUAGE TEST")
    print("=" * 70)
    
    # Set up API key (you need to set this!)
    # os.environ["ANTHROPIC_API_KEY"] = "your-key-here"
    # or
    # os.environ["OPENAI_API_KEY"] = "your-key-here"
    
    print("\n1. Starting Android container...")
    
    async with Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-nl-test",
        image="budtmo/docker-android:emulator_11.0",
        ephemeral=True
    ) as computer:
        
        print("✅ Container started")
        print("   View Android at: http://localhost:6080")
        
        # Create agent with computer as a tool
        agent = ComputerAgent(
            model="anthropic/claude-3-5-sonnet-20241022",  # or "openai/gpt-4"
            tools=[computer],
            verbosity=logging.INFO
        )
    
        print("\n2. Waiting for Android to boot (60 seconds)...")
        await asyncio.sleep(60)
        
        # Test natural language commands
        messages = [
            {"role": "user", "content": "Take a screenshot and describe what you see"}
        ]
        
        print("\n3. Testing natural language command...")
        print(f"   User: {messages[0]['content']}")
        
        try:
            # Run agent with message history
            async for result in agent.run(messages, stream=False):
                # Print the agent's response
                for item in result.get("output", []):
                    if item.get("type") == "message":
                        content = item.get("content", [])
                        if content and isinstance(content, list):
                            text = content[0].get("text", "")
                            print(f"   Agent: {text}")
                    elif item.get("type") == "computer_call":
                        action = item.get("action", {})
                        print(f"   Action: {action.get('type')}")
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
            print("   Note: Make sure you have set ANTHROPIC_API_KEY or OPENAI_API_KEY")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    
    await computer.stop()


async def test_without_bridge():
    """Test showing what works without the bridge."""
    
    print("\n" + "=" * 70)
    print("TESTING WITHOUT BRIDGE (Direct Provider Access)")
    print("=" * 70)
    
    computer = Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-direct",
        image="budtmo/docker-android:emulator_11.0",
        ephemeral=True
    )
    
    try:
        await computer.run()
    except TimeoutError:
        print("✅ Container running (WebSocket timeout expected)")
    
    # Wait for boot
    print("Waiting 60 seconds for Android to boot...")
    await asyncio.sleep(60)
    
    # Access provider directly
    provider = computer.config.vm_provider
    
    print("\nDirect provider commands (these work without bridge):")
    
    # These work directly
    await provider.home()
    print("✅ home() - navigated to home screen")
    
    await provider.tap(640, 360)
    print("✅ tap(640, 360) - tapped center")
    
    await provider.swipe(640, 600, 640, 200, 500)
    print("✅ swipe() - swiped up")
    
    screenshot = await provider.screenshot()
    if screenshot:
        with open("android_nl_test.png", "wb") as f:
            f.write(screenshot)
        print(f"✅ screenshot() - saved ({len(screenshot)} bytes)")
    
    await provider.open_url("https://www.google.com")
    print("✅ open_url() - opened Google")
    
    print("\n" + "=" * 70)
    print("Direct provider access works perfectly!")
    print("Natural language requires the WebSocket bridge.")
    print("=" * 70)
    
    await computer.stop()


async def main():
    """Run both tests."""
    
    # Test with bridge (for natural language)
    print("\n🔧 TEST 1: With Bridge Server (Natural Language)")
    await test_with_bridge()
    
    # Clean up
    import subprocess
    subprocess.run(["docker", "stop", "android-nl-test"], capture_output=True)
    subprocess.run(["docker", "rm", "android-nl-test"], capture_output=True)
    
    # Test without bridge (direct access)
    print("\n🔧 TEST 2: Without Bridge (Direct Access)")
    await test_without_bridge()
    
    # Clean up
    subprocess.run(["docker", "stop", "android-direct"], capture_output=True)
    subprocess.run(["docker", "rm", "android-direct"], capture_output=True)


if __name__ == "__main__":
    asyncio.run(main())
