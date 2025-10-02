# Android Agent Setup Guide

Complete guide to using natural language AI control with Android emulator.

## 🔍 Current Status Check

### ✅ What's Working:
1. **Container Management** - Docker container starts/stops correctly
2. **Android Emulator** - Boots successfully (60-120 seconds)
3. **ADB Access** - Direct ADB commands work via provider methods
4. **Web VNC** - Visual access at http://localhost:6080
5. **Android Bridge** - WebSocket server implementation exists

### ⚠️ What Needs Verification:
1. **WebSocket Integration** - The `android_bridge.py` is installed but may not be fully integrated with the Computer SDK's interface layer
2. **Agent-to-ADB Translation** - Natural language → Computer SDK → ADB command flow

### 🔧 Architecture:

```
User Natural Language
    ↓
ComputerAgent (Anthropic Claude)
    ↓
Computer SDK Interface (WebSocket)
    ↓
android_bridge.py (Port 8000) ← **POTENTIAL GAP**
    ↓
ADB Commands (docker exec)
    ↓
Android Emulator
```

**The Issue:** The Computer SDK expects a WebSocket server at `ws://localhost:8000/ws` that implements the computer-server protocol. Your `android_bridge.py` provides this, but it may not be fully connected.

---

## 🚀 Setup Instructions

### Step 1: Install Prerequisites

```bash
# Ensure Docker is installed and running
docker --version

# Install Python packages (if not already installed)
cd /Users/devpatel/Documents/GitHub/cua
pip install -e libs/python/computer
pip install -e libs/python/agent
pip install -e libs/python/core
```

### Step 2: Set Anthropic API Key

**Option A: Environment Variable (Recommended)**
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"
```

**Option B: Create .env file**
```bash
# In the project root
echo "ANTHROPIC_API_KEY=sk-ant-api03-your-key-here" > .env
```

**Option C: In Python code (Not recommended for security)**
```python
import os
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-api03-your-key-here"
```

### Step 3: Verify API Key

```bash
# Check if set
echo $ANTHROPIC_API_KEY

# Or in Python
python -c "import os; print('API Key:', os.getenv('ANTHROPIC_API_KEY', 'NOT SET'))"
```

---

## 🎯 Usage Methods

### Method 1: Using the Example Script (Recommended)

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Run the interactive agent
python android_agent_example.py
```

This will:
1. Start Android container
2. Wait for emulator to boot
3. Start interactive prompt
4. Accept natural language commands

### Method 2: Direct Provider Access (No Agent)

If the WebSocket bridge isn't working, you can use direct ADB commands:

```python
import asyncio
import logging
from computer import Computer
from computer.providers.base import VMProviderType

async def direct_control():
    computer = Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-test",
        verbosity=logging.INFO,
        ephemeral=True
    )
    
    await computer.run()
    
    # Get direct provider access
    provider = computer.config.vm_provider
    
    # Direct ADB commands (no AI)
    await provider.home()
    await provider.open_app("com.android.settings")
    await provider.tap(640, 360)
    await provider.type_text("Hello Android")
    
    await computer.stop()

asyncio.run(direct_control())
```

### Method 3: Custom Agent Script

```python
import asyncio
import logging
import os
from agent import ComputerAgent
from computer import Computer
from computer.providers.base import VMProviderType

async def custom_task():
    async with Computer(
        os_type="linux",
        provider_type=VMProviderType.ANDROID,
        name="android-task",
        verbosity=logging.INFO,
        ephemeral=True
    ) as computer:
        
        # Wait for boot
        await asyncio.sleep(90)
        
        agent = ComputerAgent(
            model="anthropic/claude-3-5-sonnet-20241022",
            tools=[computer],
            verbosity=logging.INFO
        )
        
        # Single task
        history = [{
            "role": "user",
            "content": "Open Settings and enable Developer Options"
        }]
        
        async for result in agent.run(history, stream=False):
            history += result["output"]

asyncio.run(custom_task())
```

---

## 🔧 Troubleshooting

### Issue: WebSocket Connection Fails

**Symptoms:**
```
TimeoutError: WebSocket connection failed
```

**Diagnosis:**
The `android_bridge.py` may not be running or not accessible.

**Fix:**
Check if the bridge is running inside the container:

```bash
docker exec android-test ps aux | grep python
```

If not running, manually start it:

```bash
docker exec -d android-test python3 /tmp/computer_server.py android-test
```

### Issue: Agent Can't Control Android

**Symptoms:**
- Agent responds but nothing happens on Android
- "Unknown computer action" errors

**Diagnosis:**
The Computer SDK interface may not be connecting to the Android bridge.

**Fix:**
Use direct provider methods instead:

```python
# Instead of agent
provider = computer.config.vm_provider
await provider.tap(x, y)
```

### Issue: Emulator Not Booting

**Symptoms:**
- VNC shows black screen
- ADB devices shows "offline"

**Fix:**
```bash
# Check container logs
docker logs android-test

# Increase wait time
await asyncio.sleep(120)  # Wait 2 minutes
```

### Issue: API Key Not Found

**Symptoms:**
```
❌ ERROR: ANTHROPIC_API_KEY environment variable not set!
```

**Fix:**
```bash
# Set in current shell
export ANTHROPIC_API_KEY="your-key"

# Or add to ~/.bashrc or ~/.zshrc
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.zshrc
source ~/.zshrc
```

---

## 📊 Verification Checklist

Run this to verify everything is working:

```bash
# 1. Check Docker
docker --version

# 2. Check Python packages
python -c "from computer import Computer; from agent import ComputerAgent; print('✅ Packages OK')"

# 3. Check API key
python -c "import os; print('✅ API Key OK' if os.getenv('ANTHROPIC_API_KEY') else '❌ API Key Missing')"

# 4. Test basic Android container
python examples/android_example.py
```

---

## 🎓 Example Commands for Agent

Once running, try these natural language commands:

**Navigation:**
- "Go to the home screen"
- "Open recent apps"
- "Swipe down to show notifications"

**Apps:**
- "Open the Settings app"
- "Launch Chrome browser"
- "Open the Calculator"

**Interaction:**
- "Tap the center of the screen"
- "Type 'hello world' in the search box"
- "Scroll down the page"

**Complex Tasks:**
- "Open Chrome and search for Python tutorials"
- "Go to Settings and enable Developer Options"
- "Open the Play Store and search for YouTube"

---

## 📝 Notes

1. **Boot Time**: Android emulator takes 60-120 seconds to fully boot. Be patient!
2. **VNC Access**: Always available at http://localhost:6080 to see what's happening
3. **Costs**: Anthropic API calls cost money. Use `max_trajectory_budget` to limit spending
4. **Screenshots**: Saved in `./android_trajectories/` directory
5. **Cleanup**: With `ephemeral=True`, container is auto-deleted on exit

---

## 🐛 Known Limitations

1. **WebSocket Bridge**: May need manual verification/fixes
2. **First Boot**: Very slow (pulling Docker image + emulator boot)
3. **Network**: Container needs internet access for Play Store, etc.
4. **Performance**: Emulator is slower than physical device

---

## 📚 File Reference

- **Provider**: `libs/python/computer/computer/providers/androiddocker/provider.py`
- **Bridge**: `libs/python/computer/computer/providers/androiddocker/android_bridge.py`
- **Example**: `examples/android_example.py`
- **Agent**: `libs/python/agent/agent/agent.py`
- **Interface**: `libs/python/computer/computer/interface/generic.py`
