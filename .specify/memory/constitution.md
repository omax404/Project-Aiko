# Aiko Desktop Project Constitution

<!-- Sync Impact Report:
- Version change: 0.0.0 -> 1.0.0
- List of modified principles: Scaffolded draft -> Zero-Trust Security, Non-Blocking Async, Unified Emotional State, Strictly Typed Protocols, Clean Decoupled Architecture
- Added sections: Technology Standards & Constraints, Verification Discipline
- Templates requiring updates:
  - .specify/templates/plan-template.md (✅ updated)
  - .specify/templates/spec-template.md (✅ updated)
  - .specify/templates/tasks-template.md (✅ updated)
- Follow-up TODOs: None
-->

## Core Principles

### I. Zero-Trust Security & HITL Gates
All inputs are validated and sanitized at the API and WebSocket boundary before reaching the LLM orchestrator. Prompt injections are normalized and blocked. Sensitive host OS and file-system commands (OPEN, TYPE, CLICK, PRESS, write-action MCPs) require explicit, non-intrusive human approval via the WebSocket confirmation gate. Raw, dynamic code execution (RUN_PYTHON) is prohibited; calculations are routed to safe allowlisted functions.

### II. Non-Blocking Asynchronous Core
The backend uses Python `asyncio` and `aiohttp`. The main event loop must remain completely responsive to maintain WebSocket heartbeats, streaming token events, and WebRTC client syncs. Heavy, synchronous, or blocking operations—such as pyautogui mouse/keyboard automation, DXCAM display capture, local Stable Diffusion rendering, and speech synthesis compilation—must be offloaded to thread or process pool executors.

### III. Unified Emotional State & Source of Truth
The Python backend serves as the absolute, single source of truth for Aiko's emotional states (Dopamine, Serotonin, Cortisol, Adrenaline). Client front-ends (desktop React, mobile Android) do not calculate emotional swings independently. Instead, they listen to state delta updates pushed by the server, ensuring perfect emotional alignment across all viewports.

### IV. Strictly Typed Event Protocols
All WebSocket communications adhere to a strict, standardized payload model containing unique request/message IDs, epoch timestamps, event types, and structured data blocks. Important state changes are verified via client acknowledgments (ACKs) to prevent race conditions.

### V. Clean Decoupled Architecture
Maintain strict modular isolation between the UI viewports, the core state machines (`chat_engine.py`, `persona.py`), and infrastructure adapters (RAG, TTS, media generation, and local tools execution). Modules must be self-contained and testable in CI/CD without external network dependencies.

## Technology Standards & Constraints
* **Backend**: Python 3.11+ using `asyncio` and `aiohttp` for high-throughput, low-latency concurrent routing.
* **Frontend**: React 18, TypeScript, Tailwind CSS, and PixiJS with Cubism 4 SDK for hardware-accelerated 2D animations.
* **Database**: ChromaDB for RAG context memory storage.
* **Mobile Client**: Native Android Kotlin app communicating via WebRTC.

## Verification Discipline
* Every bug fix, refactor, or new feature requires corresponding unit tests in the `tests/` directory.
* Direct network calls during tests are forbidden; all external APIs, database lookups, and AI model queries must be mocked.
* The frontend must compile successfully (`npx tsc --noEmit`) before any code is pushed to production.

## Governance
* This constitution is the supreme authority for the codebase.
* Amendments require documented justification, a corresponding version bump, and a verified migration plan.
* All code reviews must explicitly verify compliance with these core principles.

**Version**: 1.0.0 | **Ratified**: 2026-07-14 | **Last Amended**: 2026-07-14
