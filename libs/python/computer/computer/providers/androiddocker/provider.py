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

    def _run_adb_command(self, adb_args: list) -> subprocess.CompletedProcess:
        """Helper method to run ADB commands inside the container. (since exec is not available in docker on mac and need via the VM)"""
        cmd = ["docker", "exec", "-i", self.container_name, "adb"] + adb_args
        if self.verbose:
            logger.info(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 and self.verbose:
            logger.error(f"ADB command failed: {result.stderr}")
        
        return result

    # ---- Container Management ----
    def start(self):
        """Start the Android emulator container."""
        cmd = [
            "docker", "run", "-d", "--privileged",
            "-p", f"6080:6080",
            "-p", f"5554:5554", 
            "-p", f"5555:5555",
            "-p", f"5900:5900",
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

    def cleanup(self):
        """Remove the container completely."""
        try:
            self.stop()
        except:
            pass  # Container might already be stopped
        
        cmd = ["docker", "rm", self.container_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Container {self.container_name} removed")

    # ---- Input Methods ----
    def tap(self, x: int, y: int) -> bool:
        """Tap at coordinates (x, y)."""
        result = self._run_adb_command(["shell", "input", "tap", str(x), str(y)])
        return result.returncode == 0

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 250) -> bool:
        """Swipe from (x1, y1) to (x2, y2)."""
        result = self._run_adb_command(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)])
        return result.returncode == 0

    def type_text(self, text: str) -> bool:
        """Type text into the current input field."""
        # Escape special characters for shell
        escaped_text = text.replace(" ", "%s").replace("'", "\\'")
        result = self._run_adb_command(["shell", "input", "text", escaped_text])
        return result.returncode == 0

    # ---- System Navigation ----
    def home(self) -> bool:
        """Press the home button."""
        result = self._run_adb_command(["shell", "input", "keyevent", "3"])
        return result.returncode == 0

    def back(self) -> bool:
        """Press the back button."""
        result = self._run_adb_command(["shell", "input", "keyevent", "4"])
        return result.returncode == 0

    def recents(self) -> bool:
        """Open recent apps."""
        result = self._run_adb_command(["shell", "input", "keyevent", "187"])
        return result.returncode == 0

    def open_notifications(self) -> bool:
        """Open the notification panel."""
        result = self._run_adb_command(["shell", "cmd", "statusbar", "expand-notifications"])
        return result.returncode == 0

    def open_quick_settings(self) -> bool:
        """Open quick settings panel."""
        result = self._run_adb_command(["shell", "cmd", "statusbar", "expand-settings"])
        return result.returncode == 0

    # ---- App Control ----
    def open_app(self, package_name: str, activity: Optional[str] = None) -> bool:
        """Open an app by package name and optional activity."""
        if activity:
            result = self._run_adb_command(["shell", "am", "start", "-n", f"{package_name}/{activity}"])
        else:
            result = self._run_adb_command(["shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"])
        return result.returncode == 0

    def open_url(self, url: str) -> bool:
        """Open a URL in the default browser."""
        result = self._run_adb_command(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url])
        return result.returncode == 0

    def is_app_installed(self, package_name: str) -> bool:
        """Check if an app is installed."""
        result = self._run_adb_command(["shell", "pm", "list", "packages", package_name])
        return package_name in result.stdout

    def kill_app(self, package_name: str) -> bool:
        """Force stop an app."""
        result = self._run_adb_command(["shell", "am", "force-stop", package_name])
        return result.returncode == 0

    def clear_app_data(self, package_name: str) -> bool:
        """Clear app data and cache."""
        result = self._run_adb_command(["shell", "pm", "clear", package_name])
        return result.returncode == 0

    # ---- Screenshot ----
    def take_screenshot(self, filename: str = "screenshot.png") -> bool:
        """Take a screenshot and save it locally."""
        # Take screenshot on device
        result1 = self._run_adb_command(["shell", "screencap", "-p", f"/sdcard/{filename}"])
        if result1.returncode != 0:
            return False
            
        # Pull to host
        cmd = ["docker", "exec", "-i", self.container_name, "adb", "pull", f"/sdcard/{filename}", f"/tmp/{filename}"]
        result2 = subprocess.run(cmd, capture_output=True, text=True)
        
        # Copy from container to host
        cmd = ["docker", "cp", f"{self.container_name}:/tmp/{filename}", filename]
        result3 = subprocess.run(cmd, capture_output=True, text=True)
        
        return result2.returncode == 0 and result3.returncode == 0

    # ---- Async stubs for BaseVMProvider interface ----
    async def __aexit__(self, exc_type, exc, tb):
        self.cleanup()

    async def get_ip(self, name: str, storage: Optional[str] = None, retry_delay: int = 2) -> str:
        return self.host

    async def get_vm(self, name: str, storage: Optional[str] = None) -> dict:
        return {"name": name, "status": "running", "provider": "android"}

    async def list_vms(self) -> list:
        return [{"name": self.container_name, "status": "running"}]

    async def run_vm(self, image: str, name: str, run_opts: dict, storage: Optional[str] = None) -> dict:
        self.container_name = name
        self.image = image
        self.start()
        return {"name": name, "status": "running"}

    async def stop_vm(self, name: str, storage: Optional[str] = None) -> dict:
        self.stop()
        return {"name": name, "status": "stopped"}

    async def update_vm(self, name: str, update_opts: dict, storage: Optional[str] = None) -> dict:
        return {"name": name, "status": "updated"}