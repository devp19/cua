# WebSocket Connection Fix Guide

## Problem Summary

The Android Docker provider is failing to connect to the WebSocket server because:

1. **The bridge script is being copied** ✅
2. **But the WebSocket server isn't starting properly** ❌

## Error Analysis

```
Could not connect to WebSocket interface at localhost:8000/ws
TimeoutError: Could not connect to localhost after 30 seconds
```

This means:
- Container starts successfully
- Bridge script (`android_bridge.py`) is copied to `/tmp/computer_server.py`
- But the WebSocket server on port 8000 isn't responding

## Possible Root Causes

### 1. Python/pip Not Available in Container
The `budtmo/docker-android` container might not have Python 3 or pip installed.

**Check:**
```bash
docker exec android-agent-demo python3 --version
docker exec android-agent-demo pip3 --version
```

### 2. websockets Module Installation Failed
Even if pip exists, the websockets module might not install correctly.

**Check:**
```bash
docker exec android-agent-demo pip3 list | grep websockets
```

### 3. Server Process Not Starting
The server might be failing silently when started with `-d` (detached mode).

**Check:**
```bash
docker exec android-agent-demo ps aux | grep computer_server
docker exec android-agent-demo cat /tmp/computer_server.log
```

### 4. Port Not Exposed
Port 8000 might not be properly mapped from container to host.

**Check:**
```bash
docker port android-agent-demo
# Should show: 8000/tcp -> 0.0.0.0:8000
```

## Diagnostic Steps

### Step 1: Run the Debug Script

```bash
python3 android_debug.py
```

This will:
- Start a fresh container
- Check Python/pip availability
- Install websockets
- Start the bridge server
- Verify it's running
- Test the connection

### Step 2: Manual Verification

If the debug script fails, manually check each component:

```bash
# 1. Start container
docker run -d --privileged --name test-android \
  -p 6080:6080 -p 8000:8000 \
  -e "EMULATOR_DEVICE=Samsung Galaxy S10" \
  -e "WEB_VNC=true" \
  budtmo/docker-android:emulator_11.0

# 2. Wait for it to start
sleep 30

# 3. Check Python
docker exec test-android python3 --version

# 4. Check if pip works
docker exec test-android pip3 --version

# 5. Install websockets
docker exec test-android pip3 install websockets

# 6. Copy bridge script
docker cp libs/python/computer/computer/providers/androiddocker/android_bridge.py \
  test-android:/tmp/computer_server.py

# 7. Start server (NOT detached, to see output)
docker exec test-android python3 /tmp/computer_server.py test-android

# You should see:
# INFO:__main__:Starting Android Bridge Server for container: test-android
# INFO:__main__:Android Bridge ready at ws://0.0.0.0:8000/ws
```

## Solutions

### Solution 1: Install Python in Container (If Missing)

If Python is not available, we need to modify the Docker image or install it at runtime:

```python
# In provider.py, before copying the bridge:
install_python = ["docker", "exec", container_name, "apt-get", "update"]
subprocess.run(install_python, capture_output=True)

install_python = ["docker", "exec", container_name, "apt-get", "install", "-y", "python3", "python3-pip"]
subprocess.run(install_python, capture_output=True)
```

### Solution 2: Use Alternative Installation Method

If pip doesn't work, install websockets from source:

```bash
docker exec container_name python3 -m ensurepip
docker exec container_name python3 -m pip install websockets
```

### Solution 3: Pre-build Custom Docker Image

Create a custom Android image with Python and websockets pre-installed:

```dockerfile
FROM budtmo/docker-android:emulator_11.0

# Install Python and websockets
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    pip3 install websockets && \
    apt-get clean

# Copy bridge script
COPY android_bridge.py /usr/local/bin/computer_server.py

# Expose WebSocket port
EXPOSE 8000

# Start both emulator and bridge server
CMD ["/bin/bash", "-c", "start-emulator.sh & python3 /usr/local/bin/computer_server.py"]
```

Build and use:
```bash
docker build -t android-cua:latest .

# Then in Computer():
Computer(
    provider_type=VMProviderType.ANDROID,
    image="android-cua:latest",
    ...
)
```

### Solution 4: Use Direct ADB Control (Workaround)

Until the WebSocket bridge is fixed, use direct ADB commands:

```bash
python3 android_agent_direct.py
```

This bypasses the WebSocket layer entirely and uses direct provider methods.

## Temporary Workaround Implementation

I've updated the code with better error handling and created alternative scripts:

### Files Created:

1. **`android_debug.py`** - Diagnostic tool to identify the exact issue
2. **`android_agent_direct.py`** - Working version using direct ADB (no WebSocket)
3. **Updated `provider.py`** - Better error handling and logging
4. **Updated `android_bridge.py`** - Better logging to `/tmp/computer_server.log`

### Usage:

**For Debugging:**
```bash
python3 android_debug.py
```

**For Direct Control (Working Now):**
```bash
python3 android_agent_direct.py
```

**For AI Agent (Once WebSocket is Fixed):**
```bash
export ANTHROPIC_API_KEY="your-key"
python3 android_agent_example.py
```

## Next Steps

1. **Run the debug script** to identify the exact failure point
2. **Check the logs** at `/tmp/computer_server.log` in the container
3. **Verify Python/pip** are available in the container
4. **Consider building a custom Docker image** with Python pre-installed

## Expected Timeline

- **Immediate**: Use `android_agent_direct.py` for direct ADB control
- **Short-term**: Fix WebSocket bridge installation issues
- **Long-term**: Create custom Docker image with everything pre-configured

## Testing Checklist

- [ ] Container starts successfully
- [ ] Port 8000 is mapped to host
- [ ] Python3 is available in container
- [ ] pip3 can install websockets
- [ ] Bridge script is copied to `/tmp/computer_server.py`
- [ ] Server process starts and stays running
- [ ] Port 8000 is listening inside container
- [ ] WebSocket connection succeeds from host
- [ ] Commands are translated to ADB correctly
- [ ] Screenshots are returned properly

## Contact

If issues persist after trying these solutions, check:
- Container logs: `docker logs android-agent-demo`
- Bridge logs: `docker exec android-agent-demo cat /tmp/computer_server.log`
- Process list: `docker exec android-agent-demo ps aux`
