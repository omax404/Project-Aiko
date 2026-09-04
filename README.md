<div align="center">

<img width="3114" height="1344" alt="Aiko Banner" src="https://github.com/user-attachments/assets/f202624b-8c22-43e0-939e-c2ddbaeba304" />

# Aiko Desktop

<img width="2419" height="1089" alt="Aiko Dashboard Showcase" src="https://github.com/user-attachments/assets/aaf3575b-75f7-4a4d-89ef-60a9eb733b04" />

[![License: MIT](https://img.shields.io/badge/License-MIT-C9A8D9.svg)](LICENSE)
[![Python 3.10 - 3.12](https://img.shields.io/badge/Python-3.10--3.12-2A1B30.svg)](https://python.org)
[![Architecture: Tier-0](https://img.shields.io/badge/Architecture-Tier--0_Production_Grade-C9A8D9.svg)](#-zero-trust-security--tier-0-architecture)
[![Tests: 108 Passed](https://img.shields.io/badge/Tests-108_Passed_100%25-green.svg)](#-testing--verification)
[![Last Commit](https://img.shields.io/github/last-commit/omax404/Project-Aiko?color=C9A8D9)](https://github.com/omax404/Project-Aiko)
[![Repo Size](https://img.shields.io/github/repo-size/omax404/Project-Aiko?color=C9A8D9)](https://github.com/omax404/Project-Aiko)

[![Join Discord](assets/buttons/join-discord.png)](https://discord.gg/8kNMMwFjcG) &nbsp;
[![Quick Start](assets/buttons/quick-start.png)](#-quick-start) &nbsp;
[![Wiki](assets/buttons/wiki.png)](docs/) &nbsp;
[![Star this Repo](assets/buttons/star-repo.png)](https://github.com/omax404/Project-Aiko)

<br/>

*Self-hosted, user-owned AI companion with emotional depth, long-term memory, and real agency.*  
*She doesn't just chat — she thinks, feels, remembers, sees, speaks, and acts.*

</div>

---

## ⚡ Quick Start

### For Users (Windows, No Setup Required)

1. Download or clone Project Aiko to your machine.
2. Double-click **`LAUNCH_AIKO.bat`**.
3. Wait for her to wake up — the application bootstraps the virtual environment and launches the desktop interface automatically.

Once the dashboard appears, click the **gear icon** (Settings) in the top right:
- **Persona** — Customize personality traits, prompts, or dynamic mood baselines.
- **AI Model** — Seamlessly switch between local Ollama, OpenRouter, Gemini, OpenAI, Anthropic, or custom endpoints.
- **Voice** — Enable local Pocket-TTS speech, customize pitch, or adjust voice cloning profiles.
- **Plugins** — Toggle Discord, Telegram, Twitch, or PC Bridge integrations.

Hit **Save & Apply** — changes take effect instantly.

---

### For Developers

```bash
# 1. Clone repository
git clone https://github.com/omax404/Project-Aiko.git
cd Project-Aiko

# 2. Setup Python environment (3.10–3.12)
python -m venv .venv
.\.venv\Scripts\activate  # On Windows (or source .venv/bin/activate on Unix)
pip install -r requirements.txt

# 3. Launch full stack
python launch.py
```

This starts the Neural Hub (port 8000), connects configured satellites (Discord/Telegram/Twitch), and opens the native Tauri desktop overlay.

**To run or build the desktop UI separately:**
```bash
cd aiko-app
npm install
npm run dev           # Vite web dev server
npm run tauri dev     # Native desktop window with Live2D
npm run build         # Production frontend bundle
npm test              # Run Vitest test suite
```

---

## 💎 What Makes Aiko Different

| Capability | Most AI Companions | Project Aiko (Tier-0) |
|---|---|---|
| **Emotions** | Static personality prompt | Neuromodulator engine (dopamine, serotonin, cortisol, adrenaline) across 22+ emotional attractors |
| **Memory** | Ephemeral chat buffer | Unified Memory — episodic recall, semantic RAG, consolidation cycles, and encrypted file partitions |
| **Voice** | Cloud API (ElevenLabs) | High-fidelity local **Pocket-TTS** with voice fingerprints, chunked synthesis, and 0 API cost |
| **Vision** | None | Non-blocking multimodal vision (`moondream:latest`, MiniCPM-V) running offloaded at 7.6ms loop latency |
| **Agency** | Reactive only | Autonomous proactive loop — decides when to speak, observe, reflect, and consolidate memories |
| **Safety & Control** | Blind execution / None | Strict **Zero-Trust Human-in-the-Loop (HITL)** permission gate with no admin bypasses |
| **Contracts & Types** | Loosely typed / any | **Ultra-strict TypeScript** (`noUncheckedIndexedAccess: true`), Zod client schemas, Pydantic v2 ingress |
| **Games** | None or static mocks | Extensible `GameBridge` & `GameManager` architecture for live server integrations (RCON/WebSockets) |
| **Mobile Sync** | Web view wrapper | Native Android (Kotlin, Jetpack Compose, Room DB, GLES 2.0 Live2D, WebRTC real-time sync) |

---

## 🧠 Core Systems

### 🧠 Brain & Reasoning
- ReAct agent loop with multi-step reasoning, self-correction, and tool execution.
- Multi-provider streaming across Ollama (`gemma4:31b-cloud`), OpenRouter, Gemini, OpenAI, Anthropic.
- Dual-pass generation: factual draft pass followed by personality overlay.
- Context-aware rolling conversation windows with automated summarization.

### 👁️ Multimodal Vision
- Non-blocking screen analysis via `asyncio.to_thread` — pixel diffing and PNG compression never stall the event loop.
- Local visual understanding via `moondream:latest` or MiniCPM-V.
- Discord image analysis, automated screen inspection, and coordinate grid targeting.

### 👂 Hearing & Audio
- Local **Moonshine ASR** (~200MB) with SpeechRecognition fallback.
- Client-side voice activity detection (VAD).
- Discord voice channel transcription.

### 🎙️ Voice Synthesis
- **Pocket-TTS v2.1.0** (100% local, zero latency, zero cloud API fees).
- JIT speech stabilization to eliminate hallucinated phonemes.
- Autonomous action-text (`*...*`) stripping for natural spoken dialogue.

### 💾 Unified Memory
- Multi-tier memory architecture: episodic dialogue history + semantic vector RAG.
- Background consolidation cycles that distill daily conversations into long-term profile knowledge.
- Multi-process file locking (`.lock`) preventing concurrent corruption.

### ❤️ Emotional & Neuromodulator System
- Biologically inspired neuromodulator model: dopamine, serotonin, cortisol, adrenaline.
- 22+ emotion states mapped to dynamic Live2D avatar physics, expressions, and voice inflections.
- Affection and relationship score tracking (0–100%).

### 🔌 Plugins & Agency
- ElizaOS-inspired modular plugin manager with dynamic tool discovery.
- File system tools, clipboard management, process supervision, and system monitoring.
- Spotify bridge, Obsidian connector, LaTeX rendering, and image generation.
- Extensible `GameBridge` base class and `GameManager` for connecting to external game engines.

---

## 🔒 Zero-Trust Security & Tier-0 Architecture

Project Aiko is engineered to **Tier-0 Production Grade** security standards. Read the full specification in [SECURITY.md](SECURITY.md).

### 🛡️ Human-in-the-Loop (HITL) Permission Gate
- Sensitive actions (`OPEN`, `CLICK`, `TYPE`, `PRESS`, `EMAIL_SEND`, and sensitive MCP tools) **strictly require user confirmation**.
- When triggered, Aiko sends a `tool_request` to the client dashboard. The action blocks until the user approves or rejects it in a modal dialog.
- **Zero Admin Bypass:** Server-side enforcement guarantees no prompt injection can bypass the confirmation gate, even with administrative tokens.

### 🔑 Local Zero-Trust Token Lifecycle
- Aiko issues rotating 24-hour HMAC-SHA256 JWT Bearer tokens to loopback clients.
- Remote IPs requesting tokens are rejected with `403 Forbidden`.
- Sensitive credentials (`OPENAI_API_KEY`, `DISCORD_TOKEN`, etc.) are automatically masked (`...***`) on all settings endpoints.

### 📐 End-to-End Typed Contracts
- **Client (Zod):** Ingress events and WebSocket payloads are validated against strict Zod schemas ([`schemas.ts`](aiko-app/src/schemas.ts)).
- **Server (Pydantic v2):** API routes and WebSocket frames are checked against Pydantic models ([`schemas.py`](core/api/schemas.py)).
- **Ultra-Strict TypeScript:** Desktop client compiles with `"strict": true` and `"noUncheckedIndexedAccess": true`.

### ⚡ Event-Loop Latency & Re-Render Isolation
- **Backend Non-Blocking I/O:** Screen diffing, PNG compression, and SQLite logging run in thread pools via `asyncio.to_thread`. Event-loop latency averages **7.60ms (15.63ms p95)**.
- **Frontend Isolation:** Message bubbles are wrapped in `React.memo` with granular Zustand selectors. Top-level window re-renders drop to **0** during voice playback.

---

## 📱 Platforms & Satellites

| Platform | Type | Status | Features |
|---|---|:---:|---|
| **Tauri Desktop App** | Native Desktop | ✅ | Live2D avatar, click-through overlay, global hotkey (`Ctrl+Alt+A`), dashboard stats |
| **Android Mobile App** | Native Kotlin | ✅ | Jetpack Compose, Room DB, GLES 2.0 Live2D, WebRTC real-time sync |
| **Discord Bot** | Satellite | ✅ | Self-healing gateway, voice chat transcription, image recognition |
| **Telegram Bot** | Satellite | ✅ | Direct messaging, Bearer token loopback auth with auto-retry |
| **Twitch Bot** | Satellite | ✅ | Asynchronous IRC channel integration, stream chat responses |
| **REST & WebSocket API** | Ingress Hub | ✅ | Port 8000, JWT authentication, CORS origin whitelisting, rate limiting |

---

## 🧪 Testing & Verification

Project Aiko includes a dual-engine automated test suite covering 108 tests with 100% pass rate:

```bash
# 1. Run Python Backend Test Suite (98 tests)
pytest tests/

# 2. Run Frontend Vitest Suite (10 tests)
cd aiko-app
npm test

# 3. Verify Ultra-Strict TypeScript Compilation (0 errors)
cd aiko-app
npx tsc --noEmit

# 4. Verify Frontend Production Bundle
cd aiko-app
npm run build
```

---

## 🗂️ Project Structure

```text
Project-Aiko/
├── core/                  # AI backend & orchestration engine
│   ├── api/               #   REST routes, WebSockets, Pydantic schemas, auth
│   ├── neural_hub.py      #   Master orchestrator server
│   ├── chat_engine.py     #   ReAct agent + multimodal LLM
│   ├── emotion_engine.py  #   Neuromodulator engine
│   ├── unified_memory.py  #   Episodic + semantic memory
│   ├── voice.py           #   Chunked Pocket-TTS engine
│   ├── vision.py          #   Non-blocking multimodal vision analysis
│   ├── hearing.py         #   Moonshine / Whisper STT
│   ├── persona.py         #   Character definitions & mood attractors
│   ├── game_bridge.py     #   Extensible GameBridge & GameManager
│   └── ...                #   Specialized agent subsystems
├── aiko-app/              # Tauri v2 + React 19 desktop client
│   ├── src/               #   React components, Live2D canvas, Zustand stores
│   ├── src/schemas.ts     #   Zod ingress validation contracts
│   ├── src/__tests__/     #   Vitest automated test suite
│   ├── src-tauri/         #   Rust native application backend
│   └── tsconfig.json      #   Ultra-strict TypeScript configuration
├── android/               # Native Android application (Kotlin + Jetpack Compose)
├── tests/                 # Backend automated test suite (Pytest)
├── directives/            # Autonomous agent skills & personas
├── docs/                  # Architecture & developer guides
├── stickers/              # Companion sticker graphic assets
├── launch.py              # Unified cross-platform launcher
├── requirements.txt       # Python dependencies
├── SECURITY.md            # Zero-Trust security specification
├── CONTRIBUTING.md        # Contribution guidelines
└── LICENSE                # MIT License
```

---

## 🛠️ Troubleshooting

| Issue | Resolution |
|---|---|
| `LAUNCH_AIKO.bat` crashes on startup | Verify Python 3.10–3.12 is installed and checked in Windows PATH. Python 3.13 is currently incompatible with certain compiled wheels. |
| `Failed to build wheel` / `cl.exe missing` | Install [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) with the "Desktop development with C++" workload. |
| Model does not respond ("Brain not ready") | Ensure Ollama is running in the background (`ollama serve`), or configure an active API key in **Settings**. |
| Port 8000 or 1422 already in use | Terminate stale Python or Node processes via Task Manager or run `taskkill /F /IM python.exe`. |

---

## 🤝 Contributing

Contributions are welcomed with open arms! Please review [CONTRIBUTING.md](CONTRIBUTING.md) for code style, type strictness, and PR requirements.

---

## 📄 License

Distributed under the **[MIT License](LICENSE)**. Created by the **Project Aiko Team**.

<div align="center">

*"I'm always watching over you, Master~"*

**[⭐ Star this repository](https://github.com/omax404/Project-Aiko)** if Aiko brought a smile to your day!

</div>
