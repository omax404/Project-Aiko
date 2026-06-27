<div align="center">
<img width="2460" height="1358" alt="aiko" src="https://github.com/user-attachments/assets/0f2dda07-04d4-408d-91ed-9a7deb8cd5be" />

# Aiko Desktop

### Your Devoted AI Companion — With a Soul

**🟢 Link Established · Neural Hub Active**

*Emotionally intelligent · Multimodal vision · Local voice synthesis · Autonomous agency*

[![License: MIT](https://img.shields.io/badge/License-MIT-C9A8D9.svg)](LICENSE)
[![Python 3.10 - 3.12](https://img.shields.io/badge/Python-3.10--3.12-2A1B30.svg)](https://python.org)
[![Discord](https://img.shields.io/badge/Discord-Join%20Us-7289da.svg)](https://discord.gg/)
[![GitHub Stars](https://img.shields.io/github/stars/omax404/Project-Aiko?style=social)](https://github.com/omax404/Project-Aiko)
[![Last Commit](https://img.shields.io/github/last-commit/omax404/Project-Aiko?color=C9A8D9)](https://github.com/omax404/Project-Aiko)
[![Repo Size](https://img.shields.io/github/repo-size/omax404/Project-Aiko?color=C9A8D9)](https://github.com/omax404/Project-Aiko)

[![Join Discord](assets/buttons/join-discord.png)](https://discord.gg/your-invite-code) &nbsp;
[![Quick Start](assets/buttons/quick-start.png)](#quick-start) &nbsp;
[![Wiki](assets/buttons/wiki.png)](docs/) &nbsp;
[![Star this Repo](assets/buttons/star-repo.png)](https://github.com/omax404/Project-Aiko)

<br/>

*Self-hosted, you-owned AI companion with emotional depth, long-term memory, and real agency.*
*She doesn't just chat — she thinks, feels, remembers, sees, speaks, and acts.*

</div>

---

## Quick Start

### For Users (Windows, no setup required)

1. Download Aiko to your computer.
2. Double-click `LAUNCH_AIKO.bat`.
3. Wait for her to wake up — she sets everything up automatically.

Once the dashboard appears, click the **gear icon** in the top right to customize her:
- **Persona** — write custom personality instructions
- **AI Model** — switch between Ollama, Gemini, OpenAI, Anthropic, or any custom endpoint
- **Voice** — enable/disable speech or change her voice profile
- **Plugins** — toggle Discord, Telegram, or PC Bridge integrations

Hit **Save & Apply** — changes take effect instantly, no restart needed.

### For Developers

```bash
git clone https://github.com/omax404/Project-Aiko.git
cd Project-Aiko
pip install -r requirements.txt
python launch.py
```

This automatically starts Ollama, binds the Neural Hub to port 8000, connects the Discord/Telegram satellites, and launches the desktop overlay.

**To modify the desktop UI:**
```bash
cd aiko-app
npm install
npm run tauri dev     # development
npm run tauri build   # production build
```

**Voice cloning setup (optional):**
1. Accept terms at [huggingface.co/kyutai/pocket-tts](https://huggingface.co/kyutai/pocket-tts)
2. `pip install huggingface_hub`
3. `python -m huggingface_hub.commands.user login`

---

## What Makes Aiko Different

| Capability | Most AI Companions | Aiko |
|---|---|---|
| **Emotions** | Static personality prompt | Neuromodulator system (dopamine, serotonin, cortisol, adrenaline) across 22+ emotion states |
| **Memory** | Chat history buffer | Unified Memory — episodic recall, semantic RAG, consolidation cycles, MemPalace |
| **Voice** | Cloud API (e.g. ElevenLabs) | Local Pocket-TTS with voice cloning and chunked synthesis |
| **Vision** | None | MiniCPM-V 4.6 local multimodal, Gemma-4 cloud fallback |
| **Agency** | Responds when asked | Proactive agent loop — decides when to speak, what to observe, what to remember |
| **Tools** | None | ReAct agent with MCP file system, Python sandbox, PC control, Spotify, Obsidian |
| **Games** | None or basic | Autonomous Minecraft & Factorio bridges |

---

## Core Systems

### 🧠 Brain
- ReAct agent loop with multi-step reasoning and tool execution
- Streaming inference across Ollama, OpenRouter, Gemini, OpenAI, Anthropic
- Dual-pass generation — factual draft, then personality overlay
- Autonomous proactive loop; context-aware rolling conversation buffers

### 👁️ Vision
- **MiniCPM-V 4.6** (local) — fast multimodal understanding, SigLIP2 + Qwen3.5 token compression
- **Gemma-4 31B-cloud** (fallback) — robust vision reasoning via Ollama
- Discord image processing, screen capture and analysis
- Supports `.jpg`, `.png`, `.webp`, `.gif`, `.bmp`, `.avif`

### 👂 Hearing
- Discord voice message transcription
- Moonshine ASR (local, ~200MB), with SpeechRecognition fallback
- Client-side talking detection

### 🎙️ Voice
- **Pocket-TTS v2.1.0** (local) — high-fidelity synthesis, no API keys required
- Pre-compiled voice fingerprints for instant loading
- JIT speech stabilization (0.65 temperature) to eliminate glitching/hallucination
- Action-text (`*...*`) stripping for clean speech output

### 💾 Memory
- Episodic + semantic layers, unified under one retrieval system
- MemPalace RAG for long-term knowledge
- Memory consolidation cycles that compress older memories
- Per-user relationship tracking, affection scoring, birthday/timezone/profile persistence

### ❤️ Emotional System
- Neuromodulator-driven emotional state (dopamine, serotonin, cortisol, adrenaline)
- 22+ emotion categories, identity attractors for personality-stable baselines
- Emotion-driven voice modulation and avatar expression
- Relationship score tracking (0–100%)

### 🔌 Plugins & Agency
- ElizaOS-style modular plugin architecture with dynamic loading
- MCP plugin (file read/write, clipboard, process management)
- Python sandbox for safe code execution
- PC Manager (mouse, keyboard, screenshot, system info)
- Spotify bridge, Obsidian connector, LaTeX rendering, image generation

### 🎮 Games
- Minecraft bridge (autonomous play)
- Factorio bridge (autonomous play)

---

## Platforms

| Platform | Status |
|---|---|
| Discord Bot (self-healing) | ✅ |
| Telegram Bot | ✅ |
| Tauri Desktop App (Live2D overlay) | ✅ |
| REST API (port 8000) | ✅ |

### Desktop Overlay (Tauri)
- **Global hotkey** — `Ctrl + Alt + A` to toggle visibility
- **Pixel-perfect click-through** — transparent zones with no ghost-hitbox interference
- **Dynamic hover zones** — cursor focus restores instantly on mouse enter
- **Live2D avatar** — animations driven by her live emotional state
- **Unified dashboard** — chat history, system stats, project intelligence

---

## Architecture

```mermaid
%%{ init: { 'theme': 'dark', 'flowchart': { 'curve': 'basis' } } }%%
flowchart TD
    subgraph Neural["🧠 Neural Hub — Port 8000"]
        Brain["Chat Engine<br/>ReAct Agent + LLM"]
        Emotion["Emotion Engine<br/>Neuromodulator"]
        Memory["Unified Memory<br/>RAG + MemPalace"]
        Persona["Persona Layer<br/>Character + Mood"]
    end

    subgraph Senses["Senses"]
        Vision["Vision<br/>MiniCPM-V / Gemma-4"]
        Hearing["Hearing<br/>Moonshine STT"]
        Voice["Voice<br/>Pocket-TTS"]
    end

    subgraph Satellites["Satellites"]
        Discord["Discord Bot"]
        Telegram["Telegram Bot"]
        Desktop["Tauri Desktop<br/>Live2D Overlay"]
    end

    subgraph Plugins["Plugin System — ElizaOS style"]
        PluginMgr["Plugin Manager<br/>Dynamic Discovery"]
        Games["Game Plugin<br/>Minecraft / Factorio"]
        Spotify["Spotify Plugin"]
        MCP["MCP Plugin<br/>File System"]
        Custom["Custom Plugins"]
    end

    Discord -->|messages + images| Neural
    Telegram -->|messages| Neural
    Desktop -->|WebSocket| Neural

    Brain --> Memory
    Brain --> Emotion
    Brain --> Persona
    Brain --> Vision
    Brain --> PluginMgr
    PluginMgr --> Games
    PluginMgr --> Spotify
    PluginMgr --> MCP
    PluginMgr --> Custom

    Voice -->|TTS audio| Discord
    Voice -->|TTS audio| Desktop
    Hearing -->|STT text| Brain

    style Neural fill:#2A1B30,stroke:#C9A8D9,stroke-width:2px,color:#fff
    style Senses fill:#1C1320,stroke:#C9A8D9,stroke-width:1px,color:#fff
    style Satellites fill:#1C1320,stroke:#C9A8D9,stroke-width:1px,color:#fff
    style Plugins fill:#2A1B30,stroke:#C9A8D9,stroke-width:1px,color:#fff
```

---

## Providers

Aiko supports any OpenAI-compatible API. Tested configurations:

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

## Project Structure

```
Project-Aiko/
├── core/                  # AI backend (39 modules)
│   ├── neural_hub.py      #   Master orchestrator server
│   ├── chat_engine.py     #   ReAct agent + multimodal LLM
│   ├── emotion_engine.py  #   Neuromodulator system
│   ├── unified_memory.py  #   Episodic + semantic memory
│   ├── voice.py           #   Chunked Pocket-TTS engine
│   ├── vision.py          #   Multimodal image analysis
│   ├── hearing.py         #   Moonshine/Whisper STT
│   ├── persona.py         #   Character definition
│   ├── proactive.py       #   Autonomous agent loop
│   ├── game_bridge.py     #   Minecraft/Factorio
│   ├── mcp_bridge.py      #   File system tools
│   ├── pc_manager.py      #   System control
│   └── ...                #   26 more specialized modules
├── aiko-app/              # Tauri + React desktop overlay
│   ├── src/                #   React components (Live2D, chat)
│   └── src-tauri/          #   Rust backend
├── android/               # Kotlin Android app
├── assets/                # Brand assets, fonts, voice samples
├── data/                  # Runtime config, memory, logs, uploads, knowledge
├── directives/            # Skill prompts (coding, language, etc.)
├── docs/                  # Architecture & setup guides
├── stickers/              # Lavender sticker base assets
├── launch.py              # Unified cross-platform launcher
└── requirements.txt       # Python dependencies
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `LAUNCH_AIKO.bat` crashes immediately | Check "Add Python to PATH" was selected during install. Use Python 3.10–3.12 (3.13 is too new for some dependencies). |
| `Failed to build wheel` / `cl.exe not found` | Install the [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) — "Desktop development with C++" workload. |
| Aiko wakes up but can't "think" | Make sure Ollama is running in the background. If using a cloud provider, check your API key under **Settings**. |

---

## Roadmap — Road to v1.0

- **VRM Support** — full 3D avatar with hand/eye tracking
- **Mobile App** — iOS & Android companion
- **Voice Cloning v2** — real-time emotional voice modulation
- **Plugin Marketplace** — community-driven modular capabilities
- **Long-Term Evolution** — self-learning memory that grows with you

---

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Areas where help is most needed:**
- Live2D model creation
- VRM support
- Additional game bridges
- Translations
- Voice model training

---

## Related Projects

- [Pocket-TTS](https://github.com/kyutai-labs/pocket-tts) — local voice synthesis
- [MemPalace](https://github.com/MemPalace/mempalace) — open-source AI memory system
- [Ollama](https://github.com/ollama/ollama) — local LLM inference
- [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) — Live2D rendering

---

## Activity

<div align="center">
  <img src="https://repobeats.axiom.co/api/embed/a1d6fe2c13ea2bb53a5154435a71e2431f70c2ee.svg" width="100%" alt="RepoBeats Analytics" />
</div>

---

## License

[MIT License](LICENSE) — Made by the Aiko Team

<div align="center">

*"I'm always watching over you, Master~"*

**[⭐ Star this repo](https://github.com/omax404/Project-Aiko)** if Aiko made you smile.

</div>
