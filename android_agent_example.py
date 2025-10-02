#!/usr/bin/env python3
"""
Android Agent Example - Natural Language Control via Anthropic Claude
This example shows how to use the ComputerAgent with Android Docker provider.

Prerequisites:
1. Docker installed and running
2. Anthropic API key set in environment variable ANTHROPIC_API_KEY
3. Python packages installed: agent, computer

Usage:
    export ANTHROPIC_API_KEY="your-api-key-here"
    python android_agent_example.py
"""

import asyncio
import logging
import os
from agent import ComputerAgent
from computer import Computer
from computer.providers.base import VMProviderType

async def main():
    """Run Android agent with natural language commands."""
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY environment variable not set!")
        print("\nPlease set your API key:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\nOr create a .env file with:")
        print("  ANTHROPIC_API_KEY=your-api-key-here")
        return
    
    print("=" * 70)
    print("ANDROID AGENT - NATURAL LANGUAGE CONTROL")
    print("=" * 70)
    print(f"\n✅ Anthropic API key found (starts with: {api_key[:10]}...)")
    
    # Create Android computer instance
    print("\n📦 Step 1: Starting Android container...")
    print("   This will take 60-120 seconds for the emulator to boot")
    print("   View progress at: http://localhost:6080")
    
    async with Computer(
        os_type="linux",  # Android runs in Linux container
        provider_type=VMProviderType.ANDROID,
        name="android-agent-demo",
        image="budtmo/docker-android:emulator_11.0",
        verbosity=logging.INFO,
        ephemeral=True,  # Clean up after exit
        display="1280x720",
        memory="4GB",
        cpu="4"
    ) as computer:
        
        print("\n✅ Container started! Waiting for Android to boot...")
        print("   (This is normal - Android emulator needs time to initialize)")
        
        # Wait for Android to fully boot
        await asyncio.sleep(90)  # Give emulator time to boot
        
        print("\n🤖 Step 2: Creating AI Agent with Anthropic Claude...")
        
        # Create agent with Android computer
        agent = ComputerAgent(
            model="anthropic/claude-3-5-sonnet-20241022",  # Claude 3.5 Sonnet
            tools=[computer],
            only_n_most_recent_images=3,  # Keep last 3 screenshots
            verbosity=logging.INFO,
            trajectory_dir="android_trajectories",  # Save screenshots here
            use_prompt_caching=True,  # Reduce API costs
            max_trajectory_budget={"max_budget": 1.0, "raise_error": False}
        )
        
        print("\n✅ Agent ready! You can now give natural language commands.")
        print("\n" + "=" * 70)
        print("INTERACTIVE MODE - Type your commands")
        print("=" * 70)
        print("\nExample commands:")
        print("  - 'Open the Settings app'")
        print("  - 'Go to the home screen'")
        print("  - 'Open Chrome and search for Python tutorials'")
        print("  - 'Swipe down to open notifications'")
        print("  - 'Type exit to quit'")
        print("\n" + "=" * 70)
        
        # Interactive loop
        history = []
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Exiting...")
                    break
                
                # Add user message to history
                history.append({"role": "user", "content": user_input})
                
                print(f"\n🤖 Agent is working on: '{user_input}'")
                print("   (This may take a few moments...)\n")
                
                # Run agent
                async for result in agent.run(history, stream=False):
                    # Add agent response to history
                    history += result["output"]
                    
                    # Print agent's text responses
                    for item in result["output"]:
                        if item.get("type") == "message":
                            content = item.get("content", [])
                            for content_item in content:
                                if content_item.get("type") == "text":
                                    text = content_item.get("text", "")
                                    if text:
                                        print(f"💬 Agent: {text}")
                
                print("\n✅ Task completed!")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Exiting...")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
                print("\nYou can continue with another command or type 'exit' to quit.")
        
        print("\n" + "=" * 70)
        print("SESSION COMPLETE")
        print("=" * 70)
        print("\nScreenshots saved in: ./android_trajectories/")
        print("Container will be cleaned up automatically (ephemeral=True)")


if __name__ == "__main__":
    asyncio.run(main())
