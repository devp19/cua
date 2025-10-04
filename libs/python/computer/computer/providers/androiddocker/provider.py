"""
Author: Dev Patel
Overview: Android Docker Provider for Cua Computer SDK
Description: Treats Android container as a Linux system with Android emulator running inside.
Notes: Android image is based on budtmo/docker-android:emulator_11.0
"""

from ..base import BaseVMProvider, VMProviderType
from ..docker.provider import DockerProvider
import asyncio
import json
import logging
import os
import subprocess
import time
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class AndroidDockerProvider(DockerProvider):
    """
    Android Docker Provider that extends the standard Docker provider.
    The container runs Linux with Android emulator and computer-server inside.
    """

    def __init__(
        self,
        port: int = 8000,
        host: str = "localhost",
        image: str = "budtmo/docker-android:emulator_11.0",
        verbose: bool = False,
        storage: Optional[str] = None,
        ephemeral: bool = True,
        vnc_port: int = 6080,
        adb_port: int = 5555,
        device_profile: str = "Samsung Galaxy S10",
        **kwargs
    ):
        super().__init__(
            host=host,
            image=image, 
            verbose=verbose,
            storage=storage,
            ephemeral=ephemeral,
            vnc_port=vnc_port
        )
        self.image = image
        self.port = port
        self.api_port = port
        self.adb_port = adb_port
        self.device_profile = device_profile
        self._android_ready = False

    @property
    def provider_type(self) -> VMProviderType:
        return VMProviderType.ANDROID

    async def run_vm(self, image: str, name: str, run_opts: Dict[str, Any], storage: Optional[str] = None) -> Dict[str, Any]:
        """Run an Android emulator container with computer-server."""
        try:
            existing_vm = await self.get_vm(name, storage)
            if existing_vm["status"] == "running":
                logger.info(f"Container {name} is already running")
                self.container_name = name
                await self._setup_android_environment(name)
                return existing_vm
            elif existing_vm["status"] in ["stopped", "paused"]:
                logger.info(f"Starting existing container {name}")
                start_cmd = ["docker", "start", name]
                result = subprocess.run(start_cmd, capture_output=True, text=True, check=True)
                self.container_name = name
                await self._wait_for_container_ready(name)
                await self._setup_android_environment(name)
                return await self.get_vm(name, storage)
            
            cmd = [
                "docker", "run", "-d", "--privileged",
                "--name", name
            ]
            
            import socket
            
            def is_port_free(port):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.bind(('', port))
                        return True
                    except:
                        return False
            
            if is_port_free(self.vnc_port):
                cmd.extend(["-p", f"{self.vnc_port}:6080"])  # Web VNC
            else:
                logger.warning(f"Port {self.vnc_port} in use, skipping VNC port mapping")
                
            if is_port_free(self.adb_port):
                cmd.extend(["-p", f"{self.adb_port}:5555"]) 
            else:
                logger.warning(f"Port {self.adb_port} in use, skipping ADB port mapping")
                
            cmd.extend(["-p", f"{self.api_port}:8000"]) 
            
            if is_port_free(5554):
                cmd.extend(["-p", "5554:5554"]) 
            else:
                logger.warning("Port 5554 in use, skipping emulator console port")
                
            if is_port_free(5900):
                cmd.extend(["-p", "5900:5900"])
            else:
                logger.warning("Port 5900 in use, skipping VNC port")
            
            if "memory" in run_opts:
                memory_limit = self._parse_memory(run_opts["memory"])
                cmd.extend(["--memory", memory_limit])
            
            if "cpu" in run_opts:
                cpu_count = str(run_opts["cpu"])
                cmd.extend(["--cpus", cpu_count])
            
            cmd.extend(["-e", f"EMULATOR_DEVICE={self.device_profile}"])
            cmd.extend(["-e", "WEB_VNC=true"])
            
            if os.path.exists("/dev/kvm"):
                cmd.extend(["--device", "/dev/kvm"])
            
            docker_image = image if image != "default" else self.image
            cmd.append(docker_image)
            
            logger.info(f"Starting Android container with command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to start container: {result.stderr}")
            
            container_id = result.stdout.strip()
            logger.info(f"Container {name} started with ID: {container_id[:12]}")
            
            self._container_id = container_id
            self.container_name = name
            self._running_containers[name] = container_id
            
            await self._wait_for_container_ready(name)
            
            await self._setup_android_environment(name)
            
            vm_info = await self.get_vm(name, storage)
            vm_info["container_id"] = container_id[:12]
            
            return vm_info
            
        except Exception as e:
            error_msg = f"Error running Android VM {name}: {e}"
            logger.error(error_msg)
            return {
                "name": name,
                "status": "error",
                "error": error_msg,
                "provider": "android"
            }

    async def _setup_android_environment(self, container_name: str):
        logger.info("Setting up Android environment...")
        
        await self._wait_for_adb_ready(container_name)
        
        await self._install_computer_server(container_name)
        
        self._android_ready = True
        logger.info("Android environment ready")

    async def _wait_for_adb_ready(self, container_name: str, timeout: int = 120) -> bool:
        logger.info("Waiting for Android emulator to boot...")
        start_time = time.time()
        
        logger.info("Waiting for emulator process to start...")
        while time.time() - start_time < 30:
            cmd = ["docker", "exec", container_name, "sh", "-c", "ps aux | grep -v grep | grep emulator"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and "emulator" in result.stdout:
                logger.info("Emulator process started")
                break
            await asyncio.sleep(2)
        
        logger.info("Waiting for device to appear in ADB...")
        while time.time() - start_time < timeout:
            try:
                cmd = ["docker", "exec", container_name, "adb", "devices"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    output = result.stdout
                    lines = output.strip().split('\n')
                    
                    if len(lines) > 1:
                        for line in lines[1:]:
                            if line.strip() and '\t' in line:
                                device, status = line.strip().split('\t')
                                if status == "device": 
                                    logger.info(f"Android device ready: {device}")
                                    
                                    logger.info("Waiting for system to stabilize...")
                                    await asyncio.sleep(5)
                                    
                                    boot_check = ["docker", "exec", container_name, "adb", "shell", "getprop", "sys.boot_completed"]
                                    boot_result = subprocess.run(boot_check, capture_output=True, text=True)
                                    if boot_result.returncode == 0 and "1" in boot_result.stdout:
                                        logger.info("Android system fully booted")
                                    
                                    return True
                                elif status == "offline":
                                    logger.debug(f"Device {device} is offline, waiting...")
                
            except Exception as e:
                logger.debug(f"Waiting for ADB: {e}")
            
            # Show progress
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0:
                logger.info(f"Still waiting for emulator... ({elapsed}s elapsed)")
            
            await asyncio.sleep(2)
        
        logger.warning(f"Android emulator did not become ready within {timeout} seconds")
        return False

    async def _install_computer_server(self, container_name: str):
       
        logger.info("Setting up Android computer-server (ADB bridge)...")
        
        test_adb = ["docker", "exec", container_name, "adb", "devices"]
        result = subprocess.run(test_adb, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("ADB is working in container")
        else:
            logger.warning("ADB not yet ready")
            return False
        
        try:
            bridge_script = os.path.join(os.path.dirname(__file__), "android_bridge.py")
            
            if os.path.exists(bridge_script):
                logger.info("Installing Android computer-server bridge...")
                copy_cmd = ["docker", "cp", bridge_script, f"{container_name}:/tmp/computer_server.py"]
                subprocess.run(copy_cmd, check=True)
                
                logger.info("Installing websockets dependency...")
                
                deps_cmd = ["docker", "exec", container_name, "pip3", "install", "-q", "--break-system-packages", "websockets"]
                deps_result = subprocess.run(deps_cmd, capture_output=True, text=True)
                
                if deps_result.returncode != 0:
                    deps_cmd = ["docker", "exec", container_name, "pip3", "install", "-q", "websockets"]
                    deps_result = subprocess.run(deps_cmd, capture_output=True, text=True)
                    
                    if deps_result.returncode != 0:
                        deps_cmd = ["docker", "exec", container_name, "pip", "install", "-q", "--break-system-packages", "websockets"]
                        deps_result = subprocess.run(deps_cmd, capture_output=True, text=True)
                        
                        if deps_result.returncode != 0:
                            logger.warning("pip install failed, trying apt-get...")
                            apt_cmd = ["docker", "exec", container_name, "apt-get", "update"]
                            subprocess.run(apt_cmd, capture_output=True)
                            apt_cmd = ["docker", "exec", container_name, "apt-get", "install", "-y", "python3-websockets"]
                            deps_result = subprocess.run(apt_cmd, capture_output=True, text=True)
                            if deps_result.returncode != 0:
                                logger.warning(f"Failed to install websockets: {deps_result.stderr}")
                            else:
                                logger.info("websockets installed via apt-get")
                else:
                    logger.info("websockets installed successfully")
                
                kill_cmd = ["docker", "exec", container_name, "pkill", "-f", "computer_server.py"]
                subprocess.run(kill_cmd, capture_output=True)
                await asyncio.sleep(1)
                
                start_cmd = [
                    "docker", "exec", "-d", container_name,
                    "python3", "/tmp/computer_server.py", container_name
                ]
                result = subprocess.run(start_cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("Android computer-server started on port 8000")
                    logger.info("Container is now agent-ready!")
                    logger.info("Natural language commands via Agent are supported")
                    
                    await asyncio.sleep(3)
                    
                    check_cmd = ["docker", "exec", container_name, "ps", "aux"]
                    check_result = subprocess.run(check_cmd, capture_output=True, text=True)
                    if "computer_server.py" in check_result.stdout:
                        logger.info("Verified: computer-server process is running")
                    else:
                        logger.warning("Warning: computer-server process not found in ps output")
                        log_cmd = ["docker", "exec", container_name, "cat", "/tmp/computer_server.log"]
                        log_result = subprocess.run(log_cmd, capture_output=True, text=True)
                        if log_result.stdout:
                            logger.warning(f"Server logs: {log_result.stdout}")
                    
                    return True
                else:
                    logger.warning(f"Could not start Android computer-server: {result.stderr}")
            else:
                logger.warning("Android bridge script not found, using direct ADB mode")
        
        except Exception as e:
            logger.warning(f"Android computer-server setup failed: {e}")
            import traceback
            logger.warning(traceback.format_exc())
        
        logger.info("Running in direct ADB mode (Agent support limited)")
        return True

    async def execute_adb_command(self, command: List[str]) -> str:
        if not self.container_name:
            raise RuntimeError("Container not initialized")
        
        cmd = ["docker", "exec", self.container_name, "adb"] + command
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"ADB command failed: {result.stderr}")
        return result.stdout
    
    # System Navigation Methods
    async def home(self) -> bool:
        """Navigate to home screen (home screen)"""
        logger.info("Navigating to home screen")
        output = await self.execute_adb_command(["shell", "input", "keyevent", "3"])
        return "Error" not in output
    
    async def back(self) -> bool:
        """Navigate back (back button)"""
        logger.info("Navigating back")
        output = await self.execute_adb_command(["shell", "input", "keyevent", "4"])
        return "Error" not in output
    
    async def recents(self) -> bool:
        """Open recent apps."""
        logger.info("Opening recent apps")
        output = await self.execute_adb_command(["shell", "input", "keyevent", "187"])
        return "Error" not in output
    
    async def open_notifications(self) -> bool:
        """Open notification panel."""
        logger.info("Opening notifications")
        output = await self.execute_adb_command(["shell", "cmd", "statusbar", "expand-notifications"])
        if "Error" in output:
            logger.info("Using swipe fallback for notifications")
            return await self.swipe(500, 0, 500, 1000, 300)
        return True
    
    async def open_quick_settings(self) -> bool:
        """Open quick settings panel."""
        logger.info("Opening quick settings")
        output = await self.execute_adb_command(["shell", "cmd", "statusbar", "expand-settings"])
        return "Error" not in output
    
    # App Control Methods
    async def open_app(self, package_name: str, activity: Optional[str] = None) -> bool:
        """Open an Android app."""
        logger.info(f"Opening app: {package_name}")
        if activity:
            # Open specific activity
            cmd = ["shell", "am", "start", "-n", f"{package_name}/{activity}"]
        else:
            # Use monkey to launch main activity
            cmd = ["shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"]
        
        output = await self.execute_adb_command(cmd)
        return "Error" not in output and "Exception" not in output
    
    async def open_url(self, url: str) -> bool:
        """Open a URL in the default browser."""
        logger.info(f"Opening URL: {url}")
        cmd = ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url]
        output = await self.execute_adb_command(cmd)
        return "Error" not in output
    
    async def is_app_installed(self, package_name: str) -> bool:
        """Check if an app is installed."""
        cmd = ["shell", "pm", "list", "packages"]
        output = await self.execute_adb_command(cmd)
        return package_name in output
    
    async def kill_app(self, package_name: str) -> bool:
        """Force stop an app."""
        logger.info(f"Killing app: {package_name}")
        cmd = ["shell", "am", "force-stop", package_name]
        output = await self.execute_adb_command(cmd)
        return "Error" not in output
    
    async def clear_app_data(self, package_name: str) -> bool:
        """Clear app data."""
        logger.info(f"Clearing data for app: {package_name}")
        cmd = ["shell", "pm", "clear", package_name]
        output = await self.execute_adb_command(cmd)
        return "Success" in output
    
    # Input Methods
    async def tap(self, x: int, y: int) -> bool:
        """Perform a tap at coordinates."""
        logger.debug(f"Tapping at ({x}, {y})")
        cmd = ["shell", "input", "tap", str(x), str(y)]
        output = await self.execute_adb_command(cmd)
        return "Error" not in output
    
    async def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        """Perform a swipe gesture."""
        logger.debug(f"Swiping from ({x1}, {y1}) to ({x2}, {y2}) in {duration_ms}ms")
        cmd = ["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)]
        output = await self.execute_adb_command(cmd)
        return "Error" not in output
    
    async def type_text(self, text: str) -> bool:
        """Type text using Android keyboard."""
        logger.debug(f"Typing text: {text[:20]}...")
        # Escape special characters for shell
        escaped = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"').replace("&", "\\&")
        cmd = ["shell", "input", "text", escaped]
        output = await self.execute_adb_command(cmd)
        return "Error" not in output
    
    async def key_event(self, keycode: int) -> bool:
        """Send a key event (e.g., 66 for Enter)."""
        logger.debug(f"Sending keycode: {keycode}")
        cmd = ["shell", "input", "keyevent", str(keycode)]
        output = await self.execute_adb_command(cmd)
        return "Error" not in output
    
    async def screenshot(self) -> Optional[bytes]:
        """Take a screenshot and return as bytes."""
        logger.info("Taking screenshot")
        cmd = ["shell", "screencap", "-p"]
        result = subprocess.run(
            ["docker", "exec", self.container_name, "adb"] + cmd,
            capture_output=True
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
        return None
