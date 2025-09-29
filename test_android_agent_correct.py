#!/usr/bin/env python3
"""
Correct Android Agent Test - Following Cua's actual patterns
Based on the official example.py from the agent library
"""

import asyncio
import logging
import os
from agent import ComputerAgent
from computer import Computer
from computer.providers.base import VMProviderType

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Test Android provider with ComputerAgent following Cua patterns."""
    
    print("=" * 70)
    print("ANDROID PROVIDER - AGENT TEST (Correct Pattern)")
    print("=" * 70)
    
    # IMPORTANT: You need to set one of these API keys!
    # os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-key"
    # os.environ["OPENAI_API_KEY"] = "your-openai-key"
    
    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")):
        print("\n⚠️  WARNING: No API key found!")
        print("Set either ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable")
        print("Without an API key, the Agent cannot use an LLM for natural language")
        return
    
    print("\n1. Starting Android container...")
    
    # Create Computer with Android provider
    computer = Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-agent-test",
        image="budtmo/docker-android:emulator_11.0",
        ephemeral=True
    )

   # 2. Manually initialize the computer
await computer.run()

# 3. Now update the WebSocket URL before the interface tries to connect
if hasattr(computer, '_interface'):
    # Update the WebSocket URL to use port 7777
    computer._interface._ws_url = "ws://localhost:7777/ws"
    print(f"✅ Updated WebSocket URL to: {computer._interface._ws_url}")
    
    # Also update the base URL if it exists
    if hasattr(computer._interface, '_base_url'):
        computer._interface._base_url = computer._interface._base_url.replace('8000', '7777')
        print(f"✅ Updated base URL to: {computer._interface._base_url}")

# 4. Now enter the async context
async with computer:
    print("✅ Android container started")
    print("   View at: http://localhost:6080")
        
        # Wait for Android to boot
        print("\n2. Waiting for Android emulator to boot (60-90 seconds)...")
        await asyncio.sleep(60)
        
        # Create ComputerAgent with the computer as a tool
        # This follows the exact pattern from example.py
        agent = ComputerAgent(
            # Choose your model:
            model="anthropic/claude-sonnet-4-20250514",  # Latest Claude
            # model="openai/gpt-4",  # Or GPT-4
            
            # Pass the computer as a tool
            tools=[computer],
            
            # Optional settings
            verbosity=logging.INFO,
            trajectory_dir="trajectories",  # Save interaction history
            only_n_most_recent_images=3,  # Limit image history
        )
        
        print("\n3. Testing with natural language...")
        print("-" * 40)
        
        # Create message history (required format for agent.run)
        history = []
        
        # Test commands
        test_prompts = [
            "Take a screenshot of the Android screen",
            "Navigate to the home screen",
            "Tell me what apps you can see"
        ]
        
        for prompt in test_prompts:
            print(f"\nUser: {prompt}")
            
            # Add user message to history
            history.append({"role": "user", "content": prompt})
            
            try:
                # Run agent with history (exact pattern from example.py)
                async for result in agent.run(history, stream=False):
                    # Add agent's response to history
                    history += result["output"]
                    
                    # Print agent's actions and responses
                    for item in result["output"]:
                        if item["type"] == "message":
                            # Agent's text response
                            if "content" in item and item["content"]:
                                text = item["content"][0].get("text", "")
                                if text:
                                    print(f"Agent: {text[:200]}...")  # Truncate long responses
                        
                        elif item["type"] == "computer_call":
                            # Computer action taken
                            action = item["action"]
                            action_type = action["type"]
                            print(f"Action: {action_type}")
                        
                        elif item["type"] == "error":
                            # Error occurred
                            print(f"Error: {item.get('message', 'Unknown error')}")
            
            except Exception as e:
                print(f"Error: {e}")
                if "API" in str(e):
                    print("Make sure your API key is valid and has credits")
                break
        
        print("\n" + "=" * 70)
        print("✅ TEST COMPLETE")
        print("=" * 70)
        
        # Test direct provider access (should always work)
        print("\n4. Testing direct provider methods (no LLM needed)...")
        provider = computer.config.vm_provider
        
        if hasattr(provider, 'home'):
            await provider.home()
            print("✅ Direct home() worked")
        
        if hasattr(provider, 'screenshot'):
            screenshot = await provider.screenshot()
            if screenshot:
                print(f"✅ Direct screenshot() worked ({len(screenshot)} bytes)")
                # Save it
                with open("android_test_screenshot.png", "wb") as f:
                    f.write(screenshot)
                print("   Saved as android_test_screenshot.png")


if __name__ == "__main__":
    asyncio.run(main())
