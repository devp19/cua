import asyncio
from computer.computer import Computer
from computer.providers.base import VMProviderType
from computer.logger import LogLevel

async def main():
    computer = Computer(
        display="1280x720",
        memory="4GB",
        cpu="4",
        os_type="linux",  # Android container runs Linux
        provider_type=VMProviderType.ANDROID, 
        name="android-test",
        verbosity=LogLevel.VERBOSE,
        ephemeral=True
    )
    try:
        await computer.run()  # launches your AndroidDockerProvider

        print("Taking screenshot...")
        screenshot = await computer.interface.screenshot()
        with open("android_agent_test_screenshot.png", "wb") as f:
            f.write(screenshot)
        print("Screenshot saved!")

        print("Tapping (400, 400)...")
        await computer.interface.left_click(400, 400)

        print("Pressing Home...")
        await computer.interface.home()

        print("Opening Google.com URL...")
        await computer.interface.open_url("https://google.com")

        print("Typing 'hello from agent!'...")
        await computer.interface.type_text("hello from agent!")

        print("Successfully completed example actions!")

    finally:
        await computer.stop()

if __name__ == "__main__":
    asyncio.run(main())
