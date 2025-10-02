# Simple Android Agent - Just Works™

No WebSocket complexity. Just: **Natural Language → ADB Commands**

## Setup (2 steps)

```bash
# 1. Install anthropic
pip install anthropic

# 2. Set API key
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"
```

## Run

```bash
python3 android_simple_agent.py
```

Wait 90 seconds for Android to boot, then:

```
> Open Settings
🤖 Processing: 'Open Settings'
💬 Agent: [{"function": "open_app", "args": {"package": "com.android.settings"}}]
   Executing: open_app({'package': 'com.android.settings'})
✅ Commands executed!

> Go to home screen
🤖 Processing: 'Go to home screen'
💬 Agent: [{"function": "home"}]
   Executing: home({})
✅ Commands executed!
```

## How It Works

1. **You type** natural language
2. **Claude translates** to ADB function calls
3. **Provider executes** the ADB commands directly
4. **Done** ✅

No WebSocket server, no bridge, no complexity.

## Architecture

```
User Input
    ↓
Claude API (translates to JSON commands)
    ↓
Direct provider.method() calls
    ↓
ADB commands (docker exec)
    ↓
Android Emulator
```

## Available Commands

The agent knows these functions:
- `home()` - Home screen
- `back()` - Back button
- `recents()` - Recent apps
- `open_app(package)` - Open app
- `open_url(url)` - Open browser
- `tap(x, y)` - Tap coordinates
- `swipe(x1, y1, x2, y2, duration)` - Swipe
- `type_text(text)` - Type text
- `key_event(keycode)` - Key press

## Example Commands

- "Open the Settings app"
- "Go to the home screen"
- "Tap in the center of the screen"
- "Type Hello World"
- "Open Chrome and go to google.com"
- "Swipe down from the top"

## Troubleshooting

**If container fails to start:**
```bash
docker rm -f android-simple-agent
python3 android_simple_agent.py
```

**View Android screen:**
http://localhost:6080

**Check if emulator is ready:**
```bash
docker exec android-simple-agent adb devices
```

## That's It

No WebSocket debugging, no bridge setup, no complexity.

Just natural language → ADB commands.
