# UI Overhaul & Plugin Architecture Tasks

- [x] Phase 1: UI Theme Overhaul
  - [x] Update Tailwind config with AIRI color palette (Dark Navy, Neon Pink, Purple, Blue)
  - [x] Apply glassmorphism styling to main UI containers
  - [x] Restyle ChatBubble to match AIRI design
  - [x] Update Sidebar and InputDock
- [x] Phase 2: Cross-Platform Configuration
  - [x] Update `tauri.conf.json` bundle settings for Windows, Mac, Linux
  - [x] Prepare Android mobile configuration structure
- [x] Phase 3: ElizaOS-Inspired Plugin Architecture
  - [x] Create `core/plugins/` directory
  - [x] Define `AikoPlugin` base interface
  - [x] Refactor `game_bridge.py` into a plugin
  - [x] Refactor `spotify_bridge.py` into a plugin
  - [x] Update `chat_engine.py` to dynamically load plugins

---
**Status**: All phases complete. Aiko is now fully modernized with an AIRI-inspired UI and a modular plugin backend.
