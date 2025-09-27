import time
import subprocess
from computer.providers.androiddocker.provider import AndroidDockerProvider

def print_section(header):
    print("\n" + "="*len(header))
    print(header)
    print("="*len(header))

if __name__ == "__main__":
    print_section("Initializing Provider")
    provider = AndroidDockerProvider(
        port=5555,
        image="budtmo/docker-android:emulator_11.0",  # Change if you use a custom image
        verbose=True,
        container_name="android-provider-test"
    )

    print_section("Starting Android Container")
    provider.start()
    print("Waiting for emulator to boot (30s)...")
    time.sleep(30)  # Allow time for emulator to finish starting

    print_section("Connecting ADB")
    subprocess.run(["adb", "connect", "localhost:5555"])
    subprocess.run(["adb", "devices"])

    print_section("Performing ADB Actions")
    print("Tap at (150, 250):", provider.tap(150, 250))
    print("Type 'hello_android':", provider.type_text("hello_android"))
    print("Go Home:", provider.home())
    print("Open Recent Apps:", provider.recents())
    print("Open Notifications:", provider.open_notifications())
    print("Open Quick Settings:", provider.open_quick_settings())

    print_section("App Control Actions")
    example_package = "com.android.settings"
    print("Is Settings installed?:", provider.is_app_installed(example_package))
    print("Open Settings app:", provider.open_app(example_package))
    print("Kill Settings app:", provider.kill_app(example_package))
    print("Clear Settings data:", provider.clear_app_data(example_package))

    print_section("Screenshot")
    provider.take_screenshot("test_screenshot.png")
    print("Saved screenshot to test_screenshot.png")

    print_section("Stopping Android Container")
    provider.stop()
    print("Done!")
