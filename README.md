<div align="center">
<img src="./assets/aiko_banner.png" width="100%" alt="Aiko Banner" />

<br/>

# 💖 Aiko Desktop 🌸

### Your Devoted AI Companion — With a Soul

**Emotionally intelligent • Multimodal vision • Local voice synthesis • Autonomous agency**

[![License: MIT](https://img.shields.io/badge/License-MIT-ff69b4.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Discord](https://img.shields.io/badge/Discord-Join%20Us-7289da.svg)](https://discord.gg/)
[![GitHub Stars](https://img.shields.io/github/stars/omax404/Project-Aiko?style=social)](https://github.com/omax404/Project-Aiko)
[![GitHub Last Commit](https://img.shields.io/github/last-commit/omax404/Project-Aiko?color=pink)](https://github.com/omax404/Project-Aiko)
[![Repo Size](https://img.shields.io/github/repo-size/omax404/Project-Aiko?color=pink)](https://github.com/omax404/Project-Aiko)

<br/>

[🎀 **Join Discord**](https://discord.gg/) &nbsp; | &nbsp; [🍓 **Quick Start**](#-quick-start) &nbsp; | &nbsp; [🍰 **Wiki**](docs/) &nbsp; | &nbsp; [🍭 **Master's Profile**](https://github.com/omax404)

<br/>

*Self-hosted, you-owned AI companion with emotional depth, long-term memory, and real agency.*
*She doesn't just chat — she thinks, feels, remembers, sees, speaks, and acts.*

</div>

---

## ✨ What Makes Aiko Different?

Unlike most AI companion projects that are glorified chatbot wrappers, Aiko is built as a **living neural ecosystem**. She has:

| Feature | Most AI Companions | Aiko |
|---|---|---|
| Emotions | Static personality prompt | **Neuromodulator system** (dopamine, serotonin, cortisol, adrenaline) with 22+ emotion states |
| Memory | Chat history buffer | **Unified Memory** with episodic recall, semantic RAG, consolidation cycles, and MemPalace |
| Voice | Cloud API (ElevenLabs) | **Local Pocket-TTS** with voice cloning + full-message chunked synthesis |
| Vision | None | **Gemma-4 multimodal** — sees images on Discord, analyzes screenshots |
| Agency | Respond when asked | **Proactive agent loop** — she decides when to speak, what to observe, what to remember |
| Tools | None | **ReAct agent** with MCP file system, Python sandbox, PC control, Spotify, Obsidian |
| Games | None or basic | **Minecraft & Factorio** bridges with autonomous play |

---

## 🏗️ Architecture

```mermaid
%%{ init: { 'theme': 'dark', 'flowchart': { 'curve': 'basis' } } }%%
flowchart TD
    subgraph Neural["🧠 Neural Hub (Port 8000)"]
        Brain["Chat Engine<br/>ReAct Agent + LLM"]
        Emotion["Emotion Engine<br/>Neuromodulator"]
        Memory["Unified Memory<br/>RAG + MemPalace"]
        Persona["Persona Layer<br/>Character + Mood"]
    end

    subgraph Senses["👁️ Senses"]
        Vision["Vision<br/>Gemma-4 Multimodal"]
        Hearing["Hearing<br/>Moonshine STT"]
        Voice["Voice<br/>Pocket-TTS"]
    end

    subgraph Satellites["🛰️ Satellites"]
        Discord["Discord Bot"]
        Telegram["Telegram Bot"]
        Desktop["Tauri Desktop<br/>Live2D Overlay"]
    end

    subgraph Plugins["🔌 Plugin System (ElizaOS style)"]
        PluginMgr["Plugin Manager<br/>Dynamic Discovery"]
        Games["Game Plugin<br/>Minecraft/Factorio"]
        Spotify["Spotify Plugin"]
        MCP["MCP Plugin<br/>File System"]
        Custom["Custom Plugins"]
    end

    Discord -->|"messages + images"| Neural
    Telegram -->|"messages"| Neural
    Desktop -->|"WebSocket"| Neural

    Brain --> Memory
    Brain --> Emotion
    Brain --> Persona
    Brain --> Vision
    Brain --> PluginMgr
    PluginMgr --> Games
    PluginMgr --> Spotify
    PluginMgr --> MCP
    PluginMgr --> Custom

    Voice -->|"TTS audio"| Discord
    Voice -->|"TTS audio"| Desktop
    Hearing -->|"STT text"| Brain

    MCP --> Brain
    Sandbox --> Brain
    PC --> Brain
    Games --> Brain
    Spotify --> Brain

    style Neural fill:#1a1a2e,stroke:#e94560,stroke-width:2px,color:#fff
    style Senses fill:#16213e,stroke:#0f3460,stroke-width:2px,color:#fff
    style Satellites fill:#0f3460,stroke:#533483,stroke-width:2px,color:#fff
    style Plugins fill:#1a1a2e,stroke:#e94560,stroke-width:1px,color:#fff
```

---

## 🎯 Capabilities

### 🧠 Brain
- 🌸 ReAct agent loop with multi-step reasoning and tool execution
- 🌸 Streaming LLM inference (Ollama, OpenRouter, Gemini, OpenAI, Anthropic)
- 🌸 Dual-pass generation (factual draft → personality overlay)
- 🌸 Autonomous proactive agent loop (she decides when to speak)
- 🌸 Context-aware conversation with rolling buffers

### 👁️ Eyes (Vision)
- 🌸 Multimodal image analysis via Gemma-4 Vision
- 🌸 Discord image processing (photos, screenshots, memes)
- 🌸 Screen capture and analysis
- 🌸 Support for `.jpg`, `.png`, `.webp`, `.gif`, `.bmp`, `.avif`

### 👂 Ears (Hearing)
- 🌸 Discord voice message transcription
- 🌸 Moonshine ASR (primary, local, ~200MB)
- 🌸 SpeechRecognition fallback (Google/Whisper)
- 🌸 Client-side talking detection

### 🎙️ Voice (Mouth)
- 🌸 Pocket-TTS local synthesis (offline, no API needed)
- 🌸 Voice cloning from audio sample
- 🌸 Full-message chunked TTS (no 300-char limit)
- 🌸 Action text `*...*` stripping (clean speech output)
- 🌸 Graceful fallback to built-in voices (alba, cosette, etc.)
- 🌸 Audio sent as Discord attachment

### 💾 Memory
- 🌸 Unified Memory with episodic + semantic layers
- 🌸 MemPalace RAG for long-term knowledge retrieval
- 🌸 Memory consolidation cycles (compress old memories)
- 🌸 Per-user relationship tracking and affection system
- 🌸 Birthday, timezone, and profile persistence

### ❤️ Emotions
- 🌸 Neuromodulator system (dopamine, serotonin, cortisol, adrenaline)
- 🌸 22+ emotion categories (love, happy, yandere, panic, victory, etc.)
- 🌸 Identity attractors (personality-stable emotional baselines)
- 🌸 Emotion-driven voice modulation and avatar expressions
- 🌸 Relationship score tracking (0-100%)

### 🤖 Plugins & Agency
- 🌸 **ElizaOS-style Plugin Architecture** — modular, dynamic tool loading
- 🌸 MCP Plugin — file read/write, clipboard, process management
- 🌸 Python Sandbox — safe code execution
- 🌸 PC Manager — mouse, keyboard, screenshot, system info
- 🌸 Spotify Bridge — now playing, queue, music awareness
- 🌸 Obsidian Connector — knowledge base integration
- 🌸 LaTeX Engine — math rendering to image
- 🌸 Image Generation — AI image creation
- [x] OpenClaw delegation — complex task handoff

### 🎮 Games
- [x] Minecraft bridge (autonomous play)
- [x] Factorio bridge (autonomous play)

### 🌐 Platforms
- [x] Discord Bot (mentions, DMs, voice messages, images, slash commands)
- [x] Telegram Bot (groups, DMs)
- [x] Tauri Desktop App (Live2D overlay, chat interface)
- [x] REST API (port 8000)

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Ollama** — [Download](https://ollama.com)
- **Node.js 18+** (for Desktop app only)

### 1. Clone & Install
```bash
git clone https://github.com/omax404/aiko.git
cd aiko
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env           # Add your API keys
cp data/config.example.json data/config.json
cp core/persona.example.py core/persona.py  # Customize her personality!
```

### 3. Launch
```bash
python start_aiko_tauri.py
```

> **What happens:** Ollama starts → Neural Hub binds to port 8000 → Discord & Telegram satellites connect → Desktop overlay launches.

### Voice Setup (Optional)
To enable voice cloning with Pocket-TTS:
1. Accept terms at [huggingface.co/kyutai/pocket-tts](https://huggingface.co/kyutai/pocket-tts)
2. `pip install huggingface_hub`
3. `python -m huggingface_hub.commands.user login`

---

## 🔌 Providers

Aiko supports any OpenAI-compatible API. Here are the tested configurations:

| Provider | Example Model | Type |
|---|---|---|
| **Ollama** (default) | `gemma4:31b-cloud` | Local |
| **OpenRouter** | `google/gemma-3-27b-it:free` | Cloud (free tier) |
| **Gemini** | `gemini-2.0-flash` | Cloud |
| **OpenAI** | `gpt-4o` | Cloud |
| **Anthropic** | `claude-sonnet-4-20250514` | Cloud |
| **DeepSeek** | `deepseek-chat` | Cloud |
| **Groq** | `llama-3.3-70b` | Cloud (fast) |
| **Any OpenAI-compatible** | — | Via `API_BASE` override |

---

## 📂 Project Structure

```
aiko/
├── core/                      # 🧠 AI Backend (37 modules)
│   ├── neural_hub.py          #    Master orchestrator server
│   ├── chat_engine.py         #    ReAct agent + multimodal LLM
│   ├── emotion_engine.py      #    Neuromodulator system
│   ├── unified_memory.py      #    Episodic + semantic memory
│   ├── voice.py               #    Chunked Pocket-TTS engine
│   ├── vision.py              #    Gemma-4 image analysis
│   ├── hearing.py             #    Moonshine/Whisper STT
│   ├── bot_manager.py         #    Discord + Telegram handler
│   ├── persona.py             #    Character definition
│   ├── proactive.py           #    Autonomous agent loop
│   ├── game_bridge.py         #    Minecraft/Factorio
│   ├── mcp_bridge.py          #    File system tools
│   ├── pc_manager.py          #    System control
│   └── ...                    #    24 more specialized modules
├── aiko-app/                  # 🖥️ Tauri + React Desktop Overlay
│   ├── src/                   #    React components (Live2D, Chat)
│   └── src-tauri/             #    Rust backend
├── assets/                    # 🎨 Live2D models, fonts, voice samples
├── data/                      # 💾 Runtime config, memory, knowledge
├── directives/                # 📋 Skill prompts (coding, language, etc.)
├── docs/                      # 📖 Architecture & setup guides
├── .github/                   # 🔧 Issue templates
├── start_aiko_tauri.py        # 🚀 Unified launcher
├── requirements.txt           # 📦 Python dependencies
├── docker-compose.yml         # 🐳 Container orchestration
└── Dockerfile                 # 🐳 Container build
```

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Areas where help is needed:**
- Live2D model creation
- VRM support
- Additional game bridges
- Mobile app (React Native / Capacitor)
- Translations
- Voice model training

---

## 🔗 Related Projects

- [Pocket-TTS](https://github.com/kyutai-labs/pocket-tts) — Local voice synthesis
- [MemPalace](https://github.com/omax404/mempalace) — Semantic memory system
- [Ollama](https://github.com/ollama/ollama) — Local LLM inference
- [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) — Live2D rendering

---

## 🗺️ Roadmap (Road to v1.0)

Aiko is a living project. Here is what's coming soon:

- 🌸 **VRM Support** — Full 3D avatar integration with hand/eye tracking
- 🍓 **Mobile App** — Companion app for iOS & Android
- 🍰 **Voice Cloning v2** — Real-time emotional voice modulation
- 🍭 **Plugin Marketplace** — Community-driven modular capabilities
- 🎀 **Long-Term Evolution** — Self-learning memory that grows with you

---

## 📈 Activity

<div align="center">
  <img src="https://repobeats.axiom.co/api/embed/a1d6fe2c13ea2bb53a5154435a71e2431f70c2ee.svg" width="100%" alt="RepoBeats Analytics" />
</div>

---

## 📜 License

[MIT License](LICENSE) — Made with 💖 by the Aiko Team

---

<div align="center">

*"I'm always watching over you, Master~"* 💖

**[⭐ Star this repo](https://github.com/omax404/Project-Aiko)** if Aiko made you smile.

<br/>

✨ *Aiko is fueled by love and high-quality data* ✨

</div>
