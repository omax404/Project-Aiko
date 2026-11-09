# Product

<!-- impeccable:product-schema 1 -->

## Platform

adaptive

## Users

Developers, students, creators, and daily desktop users who want an expressive, private, always-available AI companion that feels alive on their screen rather than living in a disconnected browser tab.

## Product Purpose

Project Aiko is an open-source, local-first Live2D desktop companion equipped with an autonomous emotion engine, long-term memory palace, proactive speech synthesis, and screen vision. She bridges the gap between cold conversational LLMs and interactive desktop character presence.

## Positioning

Unlike cloud-locked character chatbots or generic developer copilots, Aiko runs completely local (or via user-owned API keys), renders responsive Live2D physics, operates without terminal setup, and maintains persistent long-term memory with strict privacy.

## Operating Context

- Windows desktop environment (Full Workspace mode or always-on-top Floating Pet Mode).
- Local LLM inference (Ollama with gemma4/qwen) or fast Cloud backends (Groq, OpenAI, Gemini).
- Background Neural Hub daemon on port 8000 with loopback token authorization.
- Real-time audio waveform reactivity and vision bridge.

## Capabilities and Constraints

- **Live2D Physics**: Real-time eye-tracking, motion physics, and emotion dynamics mapped to LLM sentiment.
- **Memory Palace**: Dual-tier storage (SQLite episodic history + ChromaDB semantic embeddings + RAG retrieval).
- **Proactive Awareness**: Contextual nudges based on idle time, system events, and music awareness.
- **Screen Vision & PC Helper**: Multi-modal vision analysis (MiniCPM-V) and optional keyboard/mouse automation.
- **Offline Voice**: Natural Piper TTS with Vivian voice model.
- **Strict Privacy**: Zero telemetry, all secrets and memory stay in local `data/`.

## Brand Commitments

- **Name**: Aiko
- **Visual Identity**: Warm Cyber-Sakura & Neo-Tokyo Editorial. Tactile elevation, readable typography, subtle organic accents—avoiding neon purple AI halos and cliché gradient titles.
- **Voice & Tone**: Warm, intelligent, playful, encouraging, and honest.

## Product Principles

1. **Local & Autonomous**: The companion belongs to the user and runs independently on their hardware.
2. **Physicality & Presence**: An animated character that breathes, reacts to mouse hover, and speaks naturally.
3. **Impeccable Craft**: No generic AI template aesthetics; intentional typography, accessible contrast, and tactile depth.
4. **Zero Terminal Friction**: Graphical setup wizard, silent launchers, and self-healing diagnostics.

## Accessibility & Inclusion

- Functional typography floor: Minimum 11px for metadata/labels, 13–15px for interactive text and chat.
- High-contrast color tokens adhering to WCAG AA on dark backgrounds.
- Screen reader announcements (`ScreenReaderAnnouncer.tsx`) for thinking and response events.
- Full keyboard hotkeys (`Ctrl+Shift+D` for diagnostics, `F1` for sidebar, `Escape` to dismiss overlays).
