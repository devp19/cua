from ..base import BaseVMProvider, VMProviderType
import logging
import subprocess
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Check if Docker is available
try:
    subprocess.run(["docker", "--version"], capture_output=True, check=True)
    HAS_DOCKER = True
except (subprocess.SubprocessError, FileNotFoundError):
    HAS_DOCKER = False



class AndroidDockerProvider(BaseVMProvider):
    """
    Manages Android devices in Docker containers via adb, implements Computer SDK automation interface.
    """

    def __init__(
        self,
        port: int = 5555,
        host: str = "localhost",
        image: str = "budtmo/docker-android:emulator_11.0",
        verbose: bool = False,
        container_name: Optional[str] = "android-container",
        **kwargs
    ):
        super().__init__()
        self.port = port
        self.host = host
        self.image = image
        self.verbose = verbose
        self.container_name = container_name

    @property
    def provider_type(self) -> VMProviderType:
        return VMProviderType.ANDROID

    # ---- async stubs for now (config after i test in vm) ----
    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get_ip(self, name: str, storage: Optional[str]=None, retry_delay: int=2) -> str:
        pass

    async def get_vm(self, name: str, storage: Optional[str]=None) -> dict:
        pass

    async def list_vms(self) -> list:
        pass

    async def run_vm(self, image: str, name: str, run_opts: dict, storage: Optional[str]=None) -> dict:
        pass

    async def stop_vm(self, name: str, storage: Optional[str]=None) -> dict:
        pass

    async def update_vm(self, name: str, update_opts: dict, storage: Optional[str]=None) -> dict:
        pass

    # ---- DO NOT MODIFY CODE BELOW THIS LINE ----

    def start(self):
        """Start the Android emulator container."""
        cmd = [
            "docker", "run", "-d",
            "-p", f"{self.port}:5555", 
            "-e", "EMULATOR_DEVICE=Samsung Galaxy S10", 
            "-e", "WEB_VNC=true",
            "--device", "/dev/kvm",
            "--name", self.container_name,
            self.image
        ]
        logger.info(f"Starting Android container: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to launch container: {result.stderr}")
            raise RuntimeError(f"Failed to start Docker container: {result.stderr}")
        logger.info(f"Container started: {result.stdout.strip()}")

    def stop(self):
        """Stop the running Android emulator container."""
        cmd = ["docker", "stop", self.container_name]
        logger.info(f"Stopping Android container: {self.container_name}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to stop container: {result.stderr}")
            raise RuntimeError(f"Failed to stop Docker container: {result.stderr}")
        logger.info(f"Container stopped: {result.stdout.strip()}")

    def tap(self, x: int, y: int):
        cmd = ["adb", "shell", "input", "tap", str(x), str(y)]
        logger.debug(f"ADB tap: {cmd}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 250):
        cmd = ["adb", "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)]
        logger.debug(f"ADB swipe: {cmd}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def type_text(self, text: str):
        cmd = ["adb", "shell", "input", "text", text]
        logger.debug(f"ADB type text: {cmd}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def home(self):
        return subprocess.run(["adb", "shell", "input", "keyevent", "3"])

    def back(self):
        return subprocess.run(["adb", "shell", "input", "keyevent", "4"])

    def recents(self):
        return subprocess.run(["adb", "shell", "input", "keyevent", "187"])

    def open_notifications(self):
        return subprocess.run(["adb", "shell", "cmd", "statusbar", "expand-notifications"])

    def open_quick_settings(self):
        return subprocess.run(["adb", "shell", "cmd", "statusbar", "expand-settings"])

    def open_app(self, package_name: str, activity: Optional[str] = None):
        if activity:
            cmd = ["adb", "shell", "am", "start", "-n", f"{package_name}/{activity}"]
        else:
            cmd = ["adb", "shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"]
        return subprocess.run(cmd)

    def open_url(self, url: str):
        cmd = ["adb", "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url]
        return subprocess.run(cmd)

    def is_app_installed(self, package_name: str) -> bool:
        cmd = ["adb", "shell", "pm", "list", "packages", package_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return package_name in result.stdout

    def kill_app(self, package_name: str):
        cmd = ["adb", "shell", "am", "force-stop", package_name]
        return subprocess.run(cmd)

    def clear_app_data(self, package_name: str):
        cmd = ["adb", "shell", "pm", "clear", package_name]
        return subprocess.run(cmd)

    def take_screenshot(self, filename: str):
        cmd = ["adb", "shell", "screencap", "-p", f"/sdcard/{filename}"]
        subprocess.run(cmd)
        # Pull to host
        subprocess.run(["adb", "pull", f"/sdcard/{filename}", filename])
