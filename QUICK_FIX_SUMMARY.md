# Quick Fix Applied - PEP 668 Issue Resolved

## Problem Identified ✅

The error was:
```
error: externally-managed-environment
× This environment is externally managed
```

**Root Cause:** The `budtmo/docker-android` container uses Python 3.12, which implements PEP 668. This prevents installing packages system-wide without the `--break-system-packages` flag.

## Solution Applied ✅

Updated `provider.py` to handle PEP 668 by trying multiple installation methods in order:

1. **pip3 with --break-system-packages** (for Python 3.11+)
2. **pip3 without flag** (for older Python)
3. **pip with --break-system-packages** (alternative)
4. **apt-get install python3-websockets** (fallback)

## What Changed

**File:** `libs/python/computer/computer/providers/androiddocker/provider.py`

**Lines 288-317:** Updated websockets installation logic to:
- Try `pip3 install --break-system-packages websockets` first
- Fall back to older methods if that fails
- Use apt-get as last resort

## Testing

Now try running again:

```bash
# Clean up old container first
docker rm -f android-direct-demo

# Run the direct control version
python3 android_agent_direct.py
```

Or for the AI agent version:

```bash
# Clean up old container
docker rm -f android-agent-demo

# Set API key
export ANTHROPIC_API_KEY="your-key"

# Run with AI agent
python3 android_agent_example.py
```

## Expected Behavior

You should now see:
```
✅ websockets installed successfully
✅ Android computer-server started on port 8000
✅ Container is now agent-ready!
✅ Verified: computer-server process is running
```

Instead of the PEP 668 error.

## If It Still Fails

Check the logs:
```bash
docker exec android-direct-demo cat /tmp/computer_server.log
docker exec android-direct-demo ps aux | grep computer_server
```

## Alternative: Use apt-get Directly

If you want to manually install websockets first:

```bash
docker exec android-direct-demo apt-get update
docker exec android-direct-demo apt-get install -y python3-websockets
```

Then restart the script.
