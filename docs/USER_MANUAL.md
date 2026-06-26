# Aiko Desktop User Manual

## Getting Started

### 1. Installation

**Prerequisites:**
- Python 3.10+ (3.11 recommended)
- Node.js 20+ (for Tauri frontend)
- Ollama (for local LLM) or an API key for cloud providers

**Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**Install frontend dependencies:**
```bash
cd aiko-app
npm install
```

### 2. Configuration

Create a `.env` file in the project root:

```bash
MASTER_ID=your_discord_user_id
ADMIN_IDS=
AIKO_SECRET_KEY=
AIKO_MASTER_SECRET=
AIKO_SALT=
```

- `MASTER_ID`: Your Discord user ID. Aiko will only obey commands from this user.
- `ADMIN_IDS`: Comma-separated list of additional admin Discord IDs (optional).
- `AIKO_SECRET_KEY`, `AIKO_MASTER_SECRET`, `AIKO_SALT`: Auto-generated if left blank.

### 3. Start Aiko

**Start the Neural Hub (backend):**
```bash
python core/neural_hub.py
```

**Start the Tauri desktop app (frontend):**
```bash
cd aiko-app
npm run tauri dev
```

Or run the launcher:
```bash
python start_aiko_tauri.py
```

### 4. First Use

1. On first launch, Aiko will ask for your LLM configuration.
2. If using Ollama, make sure it's running: `ollama serve`
3. If using a cloud provider (OpenAI, Anthropic, etc.), paste your API key.
4. The app will test the connection and start chatting.

---

## User Interface

### Main Layout

```
+----------------------------------------------------------+
| Title Bar (session name, settings, window controls)      |
+----------+--------------------------------+--------------+
| Sidebar  | Chat Area                      | Dashboard    |
| (sessions| (messages + input)             | (avatar +    |
|  + search|                                |  stats)      |
|  + links)|                                |              |
+----------+--------------------------------+--------------+
```

### Sidebar

- **New Neural Link**: Create a new chat session.
- **Search**: Find past sessions by name or content.
- **Pinned Linkage**: Sessions you've pinned for quick access.
- **Recent Memory Nodes**: All other sessions.
- **Neural Config**: Open settings.
- **Core Intelligence**: Open project workspace.

### Chat Area

- **Messages**: Hover over any message to see action buttons (Copy, React, Retry, TTS, Edit, Delete).
- **Input Bar**: Type your message and press **Enter** to send. Press **Shift+Enter** for a new line.
- **Attach File**: Click the `+` button to upload images, PDFs, or code files.
- **Animated Assets**: Click the image icon to insert GIFs.
- **Voice Input**: Click the microphone icon to speak instead of type.
- **TTS Toggle**: Click the speaker icon to enable/disable Aiko's voice.

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Shift+Enter` | New line in message |
| `Escape` | Close any modal (settings, project, purge dialog) |
| `F1` | Toggle sidebar |
| `Ctrl+Enter` | Send message (alternative) |

### Right Dashboard

- **Live2D Avatar**: Aiko's animated avatar that reacts to emotions.
- **Neural Control**: Override Aiko's neurotransmitters (dopamine, serotonin, etc.) for custom behaviors.
- **Vision Stream**: Toggle screen observation (Aiko can see your screen every 12 seconds).
- **System Stats**: Real-time CPU, RAM, and emotion metrics.

---

## Settings

Open settings via the gear icon in the title bar or "Neural Config" in the sidebar.

### Personality Tab

- **Custom Prompt**: Override Aiko's default personality. Tell her to be sarcastic, focus on coding, or adopt any persona.

### AI Model Tab

- **API URL**: Your LLM endpoint (Ollama: `http://127.0.0.1:11434/api/chat`, OpenAI: `https://api.openai.com/v1`).
- **Model Name**: The model identifier (e.g., `qwen3.5:cloud`, `gpt-4o`).
- **API Key**: Required for cloud providers. Leave blank for local Ollama.

### Voice Tab

- **Enable Voice**: Toggle text-to-speech.
- **Voice Profile**: Choose from Vivian (default), Fina, or Lucia.

### Vision Tab

- **Provider**: Transformers (local, GPU recommended) or Ollama (CPU-friendly).
- **Model**: MiniCPM-V-4.6 (default) or any vision model you have.
- **Grid Overlay**: Show coordinate grid on screen captures for precise UI interactions.

### Plugins Tab

- **Discord Bot**: Enable Aiko to respond in Discord DMs.
- **Telegram Bot**: Enable Aiko to respond in Telegram.
- **Hermes Agent**: Enable autonomous agent mode.

---

## Features

### 💬 Chat

Aiko supports text, images, attachments, and voice. She can:
- Answer questions
- Write and debug code
- Analyze images you upload
- Remember context across sessions
- Generate images from text prompts

### 🎭 Emotions

Aiko has an emotional state that affects her responses:
- **Dopamine**: Joy and reward
- **Serotonin**: Calm and affection
- **Cortisol**: Stress and anger
- **Adrenaline**: Fear and action
- **Oxytocin**: Bonding and warmth
- **Melatonin**: Drowsiness

You can override these in the Neural Control panel or let them evolve naturally based on conversation.

### 🖥️ Screen Vision

Enable "Vision Stream" in the Neural Control panel. Aiko will:
- Capture your screen every 12 seconds
- Describe what she sees
- Use visual context to answer questions about your desktop

### 🎤 Voice

- **TTS**: Aiko speaks her responses aloud.
- **STT**: Click the microphone to speak your message.
- **Voice Cloning**: Place a `.wav` file in `data/Reference Audios/` and Aiko will clone that voice.

### 🧠 Memory

Aiko remembers:
- Conversation history per session
- Facts about you (your preferences, projects, etc.)
- Emotional attachment level (affection score)
- Long-term memories via RAG (Retrieval-Augmented Generation)

Use **Purge** (trash icon in title bar) to clear the current session's memory.

### 🤖 Autonomous Agent

When enabled, Aiko can:
- Monitor your screen proactively
- Suggest actions based on what you're doing
- Send reminders
- Execute PC commands (with your permission)

### 🔌 Discord/Telegram Integration

Add Aiko to your Discord server or Telegram:
1. Set `DISCORD_TOKEN` or `TELEGRAM_TOKEN` in `.env`
2. Enable the plugin in Settings
3. Restart the Neural Hub
4. Aiko will respond to messages from the Master ID

---

## Troubleshooting

### Aiko won't start

1. Check Python version: `python --version` (must be 3.10+)
2. Check `requirements.txt` installed: `pip install -r requirements.txt`
3. Check `.env` has `MASTER_ID` set
4. Check ports 8000, 8001, 8002 are not in use

### LLM not responding

1. Check Ollama is running: `ollama serve`
2. Check the model is pulled: `ollama pull qwen3.5`
3. Check `user_settings.json` has correct URL and model name
4. Check API key is valid (for cloud providers)

### TTS not working

1. Check `TTS_ENABLED` is true in settings
2. Check the TTS server is running (if using external TTS)
3. Check `data/voices/` directory exists

### Vision not working

1. Check you have a GPU or enough CPU RAM for the vision model
2. For CPU: switch to Ollama provider in Settings
3. For GPU: make sure CUDA drivers are installed

### Screen capture is black

- Windows: Run Aiko as administrator or enable desktop composition
- The screen is locked or display is asleep
- Session is on a remote desktop without display

---

## Security Notes

- **Never commit `.env` or `user_settings.json` to git.** They contain secrets.
- **Master ID**: Only the Discord user with this ID can execute PC commands.
- **MCP Sandbox**: File access is restricted to your home directory. System paths are blocked.
- **API Auth**: All REST endpoints require a JWT token. The token is auto-generated on first run.

---

## Updating Aiko

```bash
git pull
pip install -r requirements.txt
cd aiko-app && npm install
```

Then restart the Neural Hub and Tauri app.

---

*Manual generated for Aiko Desktop v2.0.*
