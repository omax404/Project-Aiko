# Aiko Desktop v3.5 — Multimodal Edition 

> Your devoted AI assistant with emotional intelligence, high-fidelity voice synthesis, and real-time vision.

## 🌟 New Features
- **Multimodal Vision** — Aiko can now "see" images sent on Discord and Telegram. She uses Gemma-4 Vision to analyze screenshots, memes, and photos.
- **Voice Intercom** — Send voice messages to Aiko on Discord! She transcribes your voice and can reply with full-length synthesized speech (no more 300-char limits).
- **Enhanced TTS** — Robust Pocket-TTS with sentence chunking for natural, long-form narration without pauses or crashes.
- **Action Stripping** — Aiko's voice engine now intelligently ignores roleplay actions like `*giggles*` while speaking, making for a much cleaner audio experience.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **Ollama** (for local LLM) — Download from [ollama.com](https://ollama.com)
- **Hugging Face Account** — Required for custom voice cloning.

### 2. Environment Setup
1. **Copy** `.env.example` to `.env` and add your Bot/API keys.
2. **Copy** `data/config.example.json` to `data/config.json`.
3. **Copy** `core/persona.example.py` to `core/persona.py`. This is where you define Aiko's personality!

### 3. Voice Setup (Crucial)
To enable the high-quality voice cloning model, you must log in to Hugging Face:
1. Accept terms at [huggingface.co/kyutai/pocket-tts](https://huggingface.co/kyutai/pocket-tts).
2. Run: `pip install huggingface_hub`
3. Run: `python -m huggingface_hub.commands.user login`
4. Paste your Access Token.

### 4. Launch
```powershell
python start_aiko_tauri.py
```

---

## 📂 Project Structure

```
Aiko Desktop/
├── core/                  # AI Backend (Brain, Voice, Vision)
│   ├── chat_engine.py     # Multimodal LLM orchestrator
│   ├── voice.py           # Chunked TTS Engine (Pocket-TTS)
│   ├── vision.py          # Image analysis & screen capture
│   ├── bot_manager.py     # Discord/Telegram satellite handler
│   └── persona.py         # Emotion & personality definition
├── aiko-app/              # React + Tauri Desktop Overlay
├── assets/                # Live2D models, fonts, and stickers
├── data/                  # Runtime config, memory, and uploads
├── .logs/                 # Real-time system logs
├── requirements.txt       # Python dependencies
└── docker-compose.yml     # Container orchestration
```

---

## 🛠️ Configuration

### LLM Providers
Aiko supports **OpenRouter**, **Ollama**, and **Gemini**.
```json
{
  "PROVIDER": "Ollama",
  "MODEL_NAME": "gemma4:31b-cloud"
}
```



---

## 📜 License
MIT License — *Devotedly crafted by the Aiko Team.*

*"I'm watching over you, Master~"* 💖
