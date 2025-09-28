"""
Simplified Android Docker Provider for Cua Computer SDK
Treats Android container as a Linux system with Android emulator running inside.
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
        **kwargs
    ):
        # Initialize parent DockerProvider with Android image
        super().__init__(
            host=host,
            image=image,  # Pass the Android image to parent
            verbose=verbose,
            storage=storage,
            ephemeral=ephemeral,
            vnc_port=vnc_port
        )
        # Override with Android-specific image if parent changed it
        self.image = image
        # Set the port attribute that might be expected by other parts of the system
        self.port = port
        self.api_port = port  # Override the default 8000 from DockerProvider if needed
        self.adb_port = adb_port
        self._android_ready = False

    @property
    def provider_type(self) -> VMProviderType:
        # Still identify as Android provider for clarity
        return VMProviderType.ANDROID

    async def run_vm(self, image: str, name: str, run_opts: Dict[str, Any], storage: Optional[str] = None) -> Dict[str, Any]:
        """Run an Android emulator container with computer-server."""
        try:
            # Check if container already exists
            existing_vm = await self.get_vm(name, storage)
            if existing_vm["status"] == "running":
                logger.info(f"Container {name} is already running")
                self.container_name = name
                await self._setup_android_environment(name)
                return existing_vm
            elif existing_vm["status"] in ["stopped", "paused"]:
                # Start existing container
                logger.info(f"Starting existing container {name}")
                start_cmd = ["docker", "start", name]
                result = subprocess.run(start_cmd, capture_output=True, text=True, check=True)
                self.container_name = name
                await self._wait_for_container_ready(name)
                await self._setup_android_environment(name)
                return await self.get_vm(name, storage)
            
            # Build docker run command for new container
            cmd = [
                "docker", "run", "-d", "--privileged",
                "--name", name
            ]
            
            # Add port mappings - check for conflicts and adjust if needed
            import socket
            
            def is_port_free(port):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    try:
                        s.bind(('', port))
                        return True
                    except:
                        return False
            
            # Map ports, skip if already in use
            if is_port_free(self.vnc_port):
                cmd.extend(["-p", f"{self.vnc_port}:6080"])  # Web VNC
            else:
                logger.warning(f"Port {self.vnc_port} in use, skipping VNC port mapping")
                
            if is_port_free(self.adb_port):
                cmd.extend(["-p", f"{self.adb_port}:5555"])  # ADB
            else:
                logger.warning(f"Port {self.adb_port} in use, skipping ADB port mapping")
                
            cmd.extend(["-p", f"{self.api_port}:8000"])  # computer-server API port (required)
            
            # Skip emulator console port if in use (5554)
            if is_port_free(5554):
                cmd.extend(["-p", "5554:5554"])  # Emulator console
            else:
                logger.warning("Port 5554 in use, skipping emulator console port")
                
            # Skip VNC port if in use (5900)
            if is_port_free(5900):
                cmd.extend(["-p", "5900:5900"])  # VNC
            else:
                logger.warning("Port 5900 in use, skipping VNC port")
            
            # Add memory limit if specified
            if "memory" in run_opts:
                memory_limit = self._parse_memory(run_opts["memory"])
                cmd.extend(["--memory", memory_limit])
            
            # Add CPU limit if specified
            if "cpu" in run_opts:
                cpu_count = str(run_opts["cpu"])
                cmd.extend(["--cpus", cpu_count])
            
            # Environment variables for Android
            cmd.extend(["-e", "EMULATOR_DEVICE=Samsung Galaxy S10"])
            cmd.extend(["-e", "WEB_VNC=true"])
            
            # Try to add KVM device if available
            if os.path.exists("/dev/kvm"):
                cmd.extend(["--device", "/dev/kvm"])
            
            # Use provided image or default
            docker_image = image if image != "default" else self.image
            cmd.append(docker_image)
            
            logger.info(f"Starting Android container with command: {' '.join(cmd)}")
            
            # Run the container
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to start container: {result.stderr}")
            
            container_id = result.stdout.strip()
            logger.info(f"Container {name} started with ID: {container_id[:12]}")
            
            # Store container info
            self._container_id = container_id
            self.container_name = name
            self._running_containers[name] = container_id
            
            # Wait for container to be ready
            await self._wait_for_container_ready(name)
            
            # Setup Android environment and computer-server
            await self._setup_android_environment(name)
            
            # Return VM info
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
        """Setup the Android environment with computer-server."""
        logger.info("Setting up Android environment...")
        
        # Wait for ADB to be ready
        await self._wait_for_adb_ready(container_name)
        
        # Install and start computer-server
        await self._install_computer_server(container_name)
        
        self._android_ready = True
        logger.info("Android environment ready")

    async def _wait_for_adb_ready(self, container_name: str, timeout: int = 60) -> bool:
        """Wait for ADB to be ready in the container."""
        logger.info("Waiting for Android emulator to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check if ADB devices shows the emulator
                cmd = ["docker", "exec", container_name, "adb", "devices"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    output = result.stdout
                    # Look for emulator or device in the output
                    if "emulator" in output or ("device" in output and "offline" not in output):
                        logger.info("Android emulator is ready")
                        return True
                
            except Exception as e:
                logger.debug(f"Waiting for ADB: {e}")
            
            await asyncio.sleep(2)
        
        logger.warning(f"Android emulator did not become ready within {timeout} seconds")
        return False

    async def _install_computer_server(self, container_name: str):
        """Install and start the computer-server in the container."""
        logger.info("Installing computer-server in Android container...")
        
        # Install required packages
        install_commands = [
            # Update package list
            ["docker", "exec", container_name, "apt-get", "update"],
            # Install Python and pip if not present
            ["docker", "exec", container_name, "apt-get", "install", "-y", "python3", "python3-pip"],
            # Install required Python packages
            ["docker", "exec", container_name, "pip3", "install", "fastapi", "uvicorn", "pillow", "python-multipart"],
        ]
        
        for cmd in install_commands:
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(f"Command failed (may be okay): {result.stderr}")
        
        # Create a computer-server that bridges to Android
        server_script = '''#!/usr/bin/env python3
"""
Computer Server for Android
Bridges Computer SDK API calls to Android ADB commands.
"""

import base64
import subprocess
import io
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from PIL import Image
import uvicorn
import asyncio
import json

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ready", "provider": "android"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "screenshot":
                # Take screenshot using ADB
                result = subprocess.run(["adb", "shell", "screencap", "-p"], 
                                      capture_output=True)
                if result.returncode == 0:
                    # Convert to base64
                    img_b64 = base64.b64encode(result.stdout).decode()
                    await websocket.send_json({
                        "success": True, 
                        "screenshot": img_b64
                    })
                else:
                    await websocket.send_json({"success": False})
            
            elif action == "click":
                x = data.get("x", 0)
                y = data.get("y", 0)
                subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])
                await websocket.send_json({"success": True})
            
            elif action == "type":
                text = data.get("text", "")
                # Escape special characters for shell
                escaped = text.replace(" ", "%s").replace("'", "\\'")
                subprocess.run(["adb", "shell", "input", "text", escaped])
                await websocket.send_json({"success": True})
            
            elif action == "swipe":
                x1 = data.get("x1", 0)
                y1 = data.get("y1", 0)
                x2 = data.get("x2", 0)
                y2 = data.get("y2", 0)
                duration = data.get("duration", 250)
                subprocess.run(["adb", "shell", "input", "swipe", 
                              str(x1), str(y1), str(x2), str(y2), str(duration)])
                await websocket.send_json({"success": True})
            
            elif action == "key":
                keycode = data.get("keycode", "")
                subprocess.run(["adb", "shell", "input", "keyevent", str(keycode)])
                await websocket.send_json({"success": True})
            
            else:
                await websocket.send_json({
                    "success": False, 
                    "error": f"Unknown action: {action}"
                })
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.post("/screenshot")
async def screenshot():
    """Take a screenshot and return as base64."""
    result = subprocess.run(["adb", "shell", "screencap", "-p"], 
                          capture_output=True)
    if result.returncode == 0:
        img_b64 = base64.b64encode(result.stdout).decode()
        return {"success": True, "screenshot": img_b64}
    return {"success": False}

@app.post("/click")
async def click(x: int, y: int):
    """Perform a tap at the given coordinates."""
    subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])
    return {"success": True}

@app.post("/type")
async def type_text(text: str):
    """Type text using the Android keyboard."""
    escaped = text.replace(" ", "%s").replace("'", "\\'")
    subprocess.run(["adb", "shell", "input", "text", escaped])
    return {"success": True}

if __name__ == "__main__":
    print("Starting Computer Server for Android on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        
        # Write the server script to the container
        script_path = "/tmp/computer_server.py"
        write_cmd = f"cat > {script_path} << 'EOF'\n{server_script}\nEOF"
        cmd = ["docker", "exec", "-i", container_name, "sh", "-c", write_cmd]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to write server script: {result.stderr}")
            return False
        
        # Make it executable
        chmod_cmd = ["docker", "exec", container_name, "chmod", "+x", script_path]
        subprocess.run(chmod_cmd, capture_output=True, text=True)
        
        # Start the server in background
        start_cmd = ["docker", "exec", "-d", container_name, "python3", script_path]
        result = subprocess.run(start_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Computer server started successfully")
            
            # Wait for the server to be ready
            await asyncio.sleep(3)
            
            # Test the server
            test_cmd = ["docker", "exec", container_name, "curl", "-s", "http://localhost:8000/health"]
            result = subprocess.run(test_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Computer server is responding")
                return True
            else:
                logger.warning("Computer server not yet responding, but may still be starting")
                return True
        else:
            logger.error(f"Failed to start server: {result.stderr}")
            return False

    # Android-specific helper methods
    async def execute_adb_command(self, command: str) -> str:
        """Execute an ADB command in the container."""
        if not self.container_name:
            raise RuntimeError("Container not initialized")
        
        cmd = ["docker", "exec", self.container_name, "adb", "shell"] + command.split()
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout

    async def open_url(self, url: str):
        """Open a URL in the Android browser."""
        return await self.execute_adb_command(f"am start -a android.intent.action.VIEW -d {url}")

    async def open_app(self, package_name: str):
        """Open an Android app by package name."""
        return await self.execute_adb_command(f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1")
