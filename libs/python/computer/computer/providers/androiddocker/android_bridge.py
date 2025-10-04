"""
Android Bridge Server - Enables Natural Language Control
This server provides the WebSocket interface that the Computer SDK expects,
translating commands to Android ADB operations.
"""

import asyncio
import json
import logging
import subprocess
import base64
import sys
import traceback
from typing import Dict, Any, Optional

try:
    import websockets
except ImportError:
    print("ERROR: websockets module not installed")
    print("Install with: pip3 install websockets")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/computer_server.log')
    ]
)
logger = logging.getLogger(__name__)


class AndroidBridge:
    """WebSocket bridge for Android control via ADB."""
    
    def __init__(self, container_name: str = "android-test"):
        self.container_name = container_name
        
    async def execute_adb(self, command: list) -> tuple:
        """Execute ADB command directly (we're already inside the container)."""
        # Use -s emulator-5554 to explicitly target the device
        cmd = ["adb", "-s", "emulator-5554"] + command
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            success = result.returncode == 0
            output = result.stdout.decode('utf-8', errors='ignore')
            error = result.stderr.decode('utf-8', errors='ignore')
            if error:
                logger.debug(f"ADB stderr: {error}")
            return success, output, result.stdout
        except Exception as e:
            logger.error(f"ADB error: {e}")
            return False, str(e), b''
    
    async def handle_message(self, websocket, message):
        """Process incoming WebSocket messages from Computer SDK."""
        try:
            data = json.loads(message)
            # SDK sends "command", but also support "action" and "type" for compatibility
            action = data.get("command") or data.get("action") or data.get("type")
            params = data.get("params", {})
            
            logger.info(f"Handling command: {action} with params: {params}")
            
            # Screenshot request
            if action in ["screenshot", "take_screenshot"]:
                success, _, image_data = await self.execute_adb(["shell", "screencap", "-p"])
                if success and image_data:
                    # Send image as base64
                    encoded = base64.b64encode(image_data).decode('utf-8')
                    response = {
                        "success": True,
                        "action": "screenshot",
                        "image": encoded,
                        "format": "png"
                    }
                else:
                    response = {"success": False, "error": "Screenshot failed"}
            
            # Click/tap action
            elif action in ["click", "left_click", "tap"]:
                # Support both direct data and params
                x = params.get("x") or data.get("x", data.get("coordinate", [0, 0])[0])
                y = params.get("y") or data.get("y", data.get("coordinate", [0, 0])[1])
                success, output, _ = await self.execute_adb(["shell", "input", "tap", str(x), str(y)])
                response = {"success": success, "action": "click", "x": x, "y": y}
            
            # Type text
            elif action in ["type", "type_text"]:
                text = data.get("text", "")
                # Escape special characters
                escaped = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
                success, output, _ = await self.execute_adb(["shell", "input", "text", escaped])
                response = {"success": success, "action": "type", "text": text}
            
            # Key press
            elif action == "key":
                key = data.get("key", "")
                # Map common keys to Android keycodes
                key_map = {
                    "Return": "66", "Enter": "66",
                    "BackSpace": "67", "Delete": "67",
                    "Tab": "61",
                    "Escape": "111",
                    "Home": "3",
                    "Back": "4"
                }
                keycode = key_map.get(key, key)
                success, output, _ = await self.execute_adb(["shell", "input", "keyevent", keycode])
                response = {"success": success, "action": "key", "key": key}
            
            # Drag/swipe
            elif action in ["drag", "swipe"]:
                x1 = data.get("start_x", data.get("from_x", 0))
                y1 = data.get("start_y", data.get("from_y", 0))
                x2 = data.get("end_x", data.get("to_x", 0))
                y2 = data.get("end_y", data.get("to_y", 0))
                duration = data.get("duration", 300)
                
                success, output, _ = await self.execute_adb([
                    "shell", "input", "swipe",
                    str(x1), str(y1), str(x2), str(y2), str(duration)
                ])
                response = {"success": success, "action": "swipe"}
            
            # Get screen size (required by SDK)
            elif action == "get_screen_size":
                success, output, _ = await self.execute_adb(["shell", "wm", "size"])
                logger.info(f"get_screen_size: success={success}, output={output}")
                if success and "x" in output:
                    # Parse "Physical size: 1080x1920"
                    size_str = output.split(":")[-1].strip()
                    width, height = map(int, size_str.split("x"))
                    response = {
                        "success": True,
                        "size": {"width": width, "height": height}
                    }
                    logger.info(f"Returning screen size: {response}")
                else:
                    response = {"success": False, "error": "Could not get screen size"}
                    logger.error(f"Failed to get screen size: {output}")
            
            # Version command (required by SDK)
            elif action == "version":
                response = {
                    "success": True,
                    "version": "1.0.0",
                    "platform": "android"
                }
            
            # Default response for unknown actions
            else:
                logger.warning(f"Unknown action: {action}")
                response = {"success": True, "action": action, "status": "ok"}
            
            # Send response back
            await websocket.send(json.dumps(response))
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = {"success": False, "error": str(e)}
            await websocket.send(json.dumps(error_response))
    
    async def handle_connection(self, websocket):
        """Handle WebSocket connection from Computer SDK."""
        logger.info(f"New connection from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
        except Exception as e:
            logger.error(f"Connection error: {e}")
    
    async def start_server(self, host="0.0.0.0", port=8000):
        """Start the WebSocket server."""
        logger.info(f"Starting Android Bridge on ws://{host}:{port}")
        
        async with websockets.serve(self.handle_connection, host, port):
            logger.info(f"Android Bridge ready at ws://{host}:{port}/ws")
            logger.info(f"Container: {self.container_name}")
            await asyncio.Future()  # Run forever


async def main():
    """Run the bridge server."""
    try:
        container_name = sys.argv[1] if len(sys.argv) > 1 else "android-test"
        logger.info(f"Starting Android Bridge Server for container: {container_name}")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"WebSocket server will listen on 0.0.0.0:8000")
        
        bridge = AndroidBridge(container_name)
        await bridge.start_server()
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
