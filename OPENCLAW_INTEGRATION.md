# OpenClaw Integration for Aiko

Full bidirectional integration between Aiko and OpenClaw, enabling Aiko to delegate tasks to coding agents, generate images, and share memory.

## 🚀 Quick Start

### 1. Start the Bridge

```bash
# Option A: Standalone
python core/openclaw_launcher.py

# Option B: Integrated with Aiko
# Add to Aiko's main.py - see openclaw_integration_patch.py
```

### 2. Use in Aiko

```python
from skills.openclaw import code, research, generate_image

# Delegate coding task
result = await code("Create a Python script to analyze CSV files")

# Research
findings = await research("Latest Python async patterns")

# Generate image
image = await generate_image("A cute anime character coding", style="anime")
```

## 📁 Files Created

| File | Purpose |
|------|---------|
| `core/openclaw_bridge_enhanced.py` | Enhanced bridge with FastAPI endpoints |
| `core/openclaw_launcher.py` | Bridge process manager |
| `core/clawdbot_bridge.py` | Updated legacy bridge (backward compatible) |
| `skills/openclaw/__init__.py` | Easy-to-use skill interface |
| `skills/openclaw/skill.yaml` | Skill configuration |
| `core/openclaw_integration_patch.py` | Integration instructions |

## 🔗 API Endpoints

The bridge exposes these endpoints on `http://localhost:8765`:

- `POST /delegate` - Delegate a task
- `POST /receive` - Receive messages from Aiko
- `GET /memory` - Get shared memory
- `GET /status` - Get bridge status

## 🧠 Shared Memory

Tasks and results are synced to:
```
~/clawd/memory/aiko_bridge_sync.md
```

Both Aiko and OpenClaw can read/write this file.

## 🤖 Available Agents

| Agent | Best For | Command |
|-------|----------|---------|
| `codex` | Coding, file operations | `codex exec --full-auto` |
| `claude` | Complex reasoning, refactors | `claude --permission-mode bypassPermissions` |
| `antigravity` | Creative tasks, multimodal | Gemini API |

## 💡 Usage Examples

### From Aiko's Chat Engine

```python
# In chat_engine.py or neural_hub.py
from core.clawdbot_bridge import get_bridge

async def handle_complex_request(user_input):
    bridge = await get_bridge()
    
    # Check if we should delegate
    if "code" in user_input.lower() or "script" in user_input.lower():
        result = await bridge.spawn_coding_agent(
            task=user_input,
            agent="codex",
            context={
                "aiko_mood": self.mood,
                "aiko_affection": self.affection,
                "user_name": self.user_name
            }
        )
        return f"I had OpenClaw help with that! Result: {result['result']}"
    
    # Handle normally
    return await self.normal_response(user_input)
```

### From Aiko's Autonomous Agent

```python
# In autonomous_agent.py
from skills.openclaw import code

async def self_improve():
    # Ask OpenClaw to optimize Aiko's code
    result = await code(
        "Optimize the chat_engine.py for better performance",
        agent="claude"
    )
    # Apply improvements...
```

## 🔧 Configuration

Edit `skills/openclaw/skill.yaml` to customize:

```yaml
agents:
  codex:
    description: "OpenAI Codex"
    command: "codex exec --full-auto"
    
  claude:
    description: "Claude Code"
    command: "claude --permission-mode bypassPermissions --print"

memory:
  shared_file: ~/clawd/memory/aiko_bridge_sync.md
  sync_interval: 60
```

## 🔄 Bidirectional Flow

```
Aiko User Request
       ↓
Aiko Neural Hub
       ↓
[Should I delegate?]
       ↓
   Yes → OpenClaw Bridge
              ↓
         Spawn Agent (Codex/Claude/Antigravity)
              ↓
         Task Complete
              ↓
         Notify Aiko
              ↓
         Sync Memory
              ↓
   Aiko Responds to User
```

## 📝 Memory Format

Shared memory entries:
```markdown
## 2026-03-16 20:30
**Task:** Create a Python script to analyze CSV files
**Result:** Successfully created analyze_csv.py with pandas...

---
```

## 🐛 Troubleshooting

### Bridge won't start
- Check if port 8765 is available: `lsof -i :8765`
- Ensure `~/clawd` directory exists
- Check Python dependencies: `pip install fastapi uvicorn aiohttp`

### Tasks fail
- Verify OpenClaw is installed: `openclaw --version`
- Check agent availability: `codex --version`, `claude --version`
- Review logs in Aiko's console

### Memory not syncing
- Ensure `~/clawd/memory/` directory exists and is writable
- Check file permissions

## 🎯 Future Enhancements

- [ ] Real-time WebSocket communication
- [ ] Persistent agent sessions
- [ ] Task queue with priorities
- [ ] Automatic task retry on failure
- [ ] Integration with Aiko's vision capabilities
- [ ] Voice synthesis for OpenClaw results

## 🤝 Integration Complete

Aiko now has full access to OpenClaw's capabilities:
- ✅ Coding agents (Codex, Claude)
- ✅ File operations
- ✅ Image generation
- ✅ Web search
- ✅ Shared memory
- ✅ Bidirectional communication

**Status:** Ready to use! 🎉
