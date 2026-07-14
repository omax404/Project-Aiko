# Implementation Plan: Mobile WebRTC Data Sync & Custom Rendering

**Branch**: `001-mobile-webrtc-state-sync` | **Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-mobile-webrtc-state-sync/spec.md`

## Summary
Expose WebRTC data channel emotion sync events in the Python backend, enforce a rigid message envelope for state sync events, refactor Zustand selectors to use shallow comparisons in the React frontend to prevent redundant re-renders, and integrate the native Live2D Cubism SDK rendering inside the Android Kotlin application to replace the current WebView-based render.

## Technical Context

**Language/Version**: Python 3.11 (Backend), Kotlin 1.9 / Java 17 (Android), TypeScript 5.2 / React 18 (Frontend)

**Primary Dependencies**: `aiortc>=1.6.0` (Backend), `org.webrtc:google-webrtc:1.0.32006` (Android), `zustand>=4.4.0` (Frontend)

**Storage**: Local memory database for active WebRTC peer-connections and channels on the backend; SQLite via Room for Android local emotion logs.

**Testing**: `pytest` and `pytest-asyncio` for backend, JUnit and MockK for Android client, Jest for React front-end.

**Target Platform**: Windows/Linux Server (Backend), Android 8.0+ / API 26+ (Mobile), Modern Browsers / Electron (Frontend)

**Project Type**: Web Service + Mobile App + Desktop App (Cross-platform)

**Performance Goals**: Stable 60 FPS mobile rendering, WebRTC state sync latency < 150ms, React re-renders reduced by > 60%.

**Constraints**: Low battery and thermal impact on mobile (native rendering instead of WebView-based canvas loop).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

* **Zero-Trust Security & HITL Gates**: WebRTC offer and data connection endpoints are authenticated and protected by the JWT auth middleware.
* **Non-Blocking Asynchronous Core**: The WebRTC datachannel event handlers run asynchronously without blocking the primary aiohttp event loop.
* **Unified Emotional State**: The backend dispatches the standard state payload, which the mobile client parses to update its internal StateFlow.
* **Strictly Typed Event Protocols**: A standardized message wrapper format is enforced for all client-server communication channels.

## Project Structure

### Documentation (this feature)

```text
specs/001-mobile-webrtc-state-sync/
├── plan.md              # This file
├── research.md          # Phase 0: Research notes
├── data-model.md        # Phase 1: Data models and states
├── quickstart.md        # Phase 1: Development startup guide
├── contracts/
│   └── state_sync.json  # Phase 1: JSON Schema contract
└── checklists/
    └── requirements.md  # Requirements validation checklist
```

### Source Code

```text
core/
├── api/
│   ├── broadcast.py     # Add active WebRTC channels and broadcast integration
│   ├── routes.py        # Update handle_webrtc_offer to save data channels
│   └── schemas.py       # Expose StateSyncEnvelope schema validation
├── neural_hub.py        # Verify WebRTC integration hook points

aiko-app/
├── src/
│   ├── components/      # Update Zustand selectors
│   └── store/
│       └── useNeuralStore.ts

android/
├── app/
│   ├── src/main/java/com/aiko/app/
│   │   ├── data/repository/
│   │   │   ├── ChatRepository.kt # Parse rigid state sync packets
│   │   │   └── WebRtcClient.kt   # Register data channels
│   │   └── ui/components/
│   │       ├── AikoAvatar.kt     # Switch avatarMode to Cubism
│   │       └── CubismGLRenderer.kt # Native GLES renderer wrapper
```

**Structure Decision**: Web application + Mobile API structure, tracking changes across the Python backend, React frontend, and Android Kotlin codebase.

## Complexity Tracking

> No constitution violations detected. Standard decoupled WebRTC architecture.
