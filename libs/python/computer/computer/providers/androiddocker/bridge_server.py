#!/usr/bin/env python3
"""
Android Bridge Server
Runs on the host and bridges Computer SDK API calls to Android ADB in container.
"""

import asyncio
import base64
import subprocess
import json
import logging
from typing import Optional
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
import uvicorn

logger = logging.getLogger(__name__)

class AndroidBridge:
    """Bridge between Computer SDK and Android ADB in Docker container."""
    
    def __init__(self, container_name: str):
        self.container_name = container_name
        self.app = FastAPI()
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/health")
        async def health():
            return {"status": "ready", "provider": "android", "container": self.container_name}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    data = await websocket.receive_json()
                    action = data.get("action")
                    
                    if action == "screenshot":
                        screenshot = await self.take_screenshot()
                        if screenshot:
                            await websocket.send_json({
                                "success": True,
                                "screenshot": screenshot
                            })
                        else:
                            await websocket.send_json({"success": False})
                    
                    elif action == "click":
                        x = data.get("x", 0)
                        y = data.get("y", 0)
                        await self.click(x, y)
                        await websocket.send_json({"success": True})
                    
                    elif action == "type":
                        text = data.get("text", "")
                        await self.type_text(text)
                        await websocket.send_json({"success": True})
                    
                    elif action == "swipe":
                        x1 = data.get("x1", 0)
                        y1 = data.get("y1", 0)
                        x2 = data.get("x2", 0)
                        y2 = data.get("y2", 0)
                        duration = data.get("duration", 250)
                        await self.swipe(x1, y1, x2, y2, duration)
                        await websocket.send_json({"success": True})
                    
                    elif action == "key":
                        keycode = data.get("keycode", "")
                        await self.key_event(keycode)
                        await websocket.send_json({"success": True})
                    
                    else:
                        await websocket.send_json({
                            "success": False,
                            "error": f"Unknown action: {action}"
                        })
                        
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                await websocket.close()
        
        @self.app.post("/screenshot")
        async def screenshot():
            """Take a screenshot and return as base64."""
            img_b64 = await self.take_screenshot()
            if img_b64:
                return {"success": True, "screenshot": img_b64}
            return {"success": False}
        
        @self.app.post("/click")
        async def click(x: int, y: int):
            """Perform a tap at the given coordinates."""
            await self.click(x, y)
            return {"success": True}
        
        @self.app.post("/type")
        async def type_text(text: str):
            """Type text using the Android keyboard."""
            await self.type_text(text)
            return {"success": True}
    
    async def take_screenshot(self) -> Optional[str]:
        """Take a screenshot using ADB in the container."""
        cmd = ["docker", "exec", self.container_name, "adb", "shell", "screencap", "-p"]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0 and result.stdout:
            return base64.b64encode(result.stdout).decode()
        return None
    
    async def click(self, x: int, y: int):
        """Perform a tap at the given coordinates."""
        cmd = ["docker", "exec", self.container_name, "adb", "shell", "input", "tap", str(x), str(y)]
        subprocess.run(cmd, capture_output=True)
    
    async def type_text(self, text: str):
        """Type text using the Android keyboard."""
        # Escape special characters for shell
        escaped = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        cmd = ["docker", "exec", self.container_name, "adb", "shell", "input", "text", escaped]
        subprocess.run(cmd, capture_output=True)
    
    async def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int):
        """Perform a swipe gesture."""
        cmd = ["docker", "exec", self.container_name, "adb", "shell", "input", "swipe",
               str(x1), str(y1), str(x2), str(y2), str(duration)]
        subprocess.run(cmd, capture_output=True)
    
    async def key_event(self, keycode: str):
        """Send a key event."""
        cmd = ["docker", "exec", self.container_name, "adb", "shell", "input", "keyevent", str(keycode)]
        subprocess.run(cmd, capture_output=True)
    
    def run(self, port: int = 8000):
        """Run the bridge server."""
        uvicorn.run(self.app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    import sys
    container_name = sys.argv[1] if len(sys.argv) > 1 else "android-container"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    print(f"Starting Android Bridge Server for container '{container_name}' on port {port}")
    bridge = AndroidBridge(container_name)
    bridge.run(port)
