# Feature Specification: Mobile WebRTC Data Sync & Custom Rendering

**Feature Branch**: `001-mobile-webrtc-state-sync`

**Created**: 2026-07-14

**Status**: Draft

**Input**: User description: "Expose WebRTC data channel emotion sync events in backend, remove offline rendering logic in Kotlin app and integrate Cubism SDK native rendering, enforce rigid message envelope in backend, and refactor Zustand selectors to use shallow comparisons in frontend"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Native Live2D Avatar Animation on Android (Priority: P1)
The mobile Android companion app displays the active Live2D avatar. The avatar animates smoothly in response to speech (lip-syncing based on voice amplitude data) and reacts physically to user interactions (touching screen regions triggers pre-defined animations/expressions).

**Why this priority**: Core value of a mobile companion app is a responsive, highly animated avatar representing the AI's persona without the lag/bandwidth overhead of video streaming.

**Independent Test**: Can be verified by running the Kotlin app on an Android emulator or device, speaking to Aiko, and confirming the avatar lips move and expressions match the conversational tone.

**Acceptance Scenarios**:
1. **Given** the Android app is connected to the backend, **When** Aiko speaks, **Then** the Live2D model mouth parameters dynamically adjust according to the amplitude envelope.
2. **Given** the Live2D model is loaded, **When** the user taps Aiko's head or body, **Then** the model plays the corresponding motion file (e.g., tap_body, tap_head) and updates the facial expression.

---

### User Story 2 - State Synchronization & WebSocket/WebRTC Protocol (Priority: P2)
The companion app (mobile and desktop) synchronizes emotional states and biometrics in real-time. When Aiko's emotional engine updates dopamine or serotonin levels, these changes are pushed immediately over the WebSocket/WebRTC channels and render on the client dashboard stats.

**Why this priority**: Eliminates discrepancy between client and backend emotional states, ensuring consistency in behavior.

**Independent Test**: Trigger an emotion state shift via backend mocks and verify that both the React dashboard gauges and the mobile state indicators update immediately.

**Acceptance Scenarios**:
1. **Given** a change in Aiko's neuro-chemicals (e.g. dopamine spike), **When** the backend dispatches a state update, **Then** the message uses a rigid, standard envelope containing `msg_id`, `timestamp`, `type`, and `payload`.
2. **Given** a state synchronization message is received on the React client, **When** the store updates, **Then** only the components subscribing to the modified keys re-render, thanks to Zustand shallow comparison selectors.

## Requirements *(mandatory)*

### Functional Requirements

* **FR-001**: The backend MUST expose a WebRTC peer-connection handler with data channel support for bi-directional state and event synchronization.
* **FR-002**: All state sync events MUST contain a rigid message envelope:
  ```json
  {
    "msg_id": "uuid-v4-string",
    "timestamp": 1783980687.916,
    "type": "EMOTION_SYNC",
    "payload": {
      "dopamine": 0.85,
      "serotonin": 0.70,
      "cortisol": 0.30,
      "adrenaline": 0.40
    }
  }
  ```
* **FR-003**: The mobile Kotlin application MUST remove the offline dummy rendering stubs and integrate the Live2D Cubism Native SDK for direct glSurfaceView drawing.
* **FR-004**: The mobile client MUST parse the WebRTC data channel events and feed voice amplitude values directly to Cubism's lip-sync parameter (`ParamMouthOpenY`).
* **FR-005**: React Zustand selectors MUST use shallow comparison (`useShallow` from `zustand/shallow`) to prevent redundant component re-renders when unrelated store properties change.

### Key Entities

* **StateSyncEnvelope**: Represents the standard message payload wrapper for all real-time events.
  * Attributes: `msg_id` (String), `timestamp` (Float), `type` (String), `payload` (JSON).
* **Live2DModelContext**: Manages the loaded Cubism model metrics (expressions, physics, mouth parameters) inside the mobile application.

## Success Criteria *(mandatory)*

### Measurable Outcomes

* **SC-001**: Mobile rendering frame rate MUST maintain stable 60 FPS under normal execution (no drop below 45 FPS during complex animations).
* **SC-002**: State synchronization delay (from backend state mutation to mobile client parameter update) MUST be under 150ms over local networks.
* **SC-003**: React component re-renders for dashboard telemetry gauges MUST drop by at least 60% after switching to Zustand shallow selectors.

## Assumptions

* The mobile device supports GLES2.0 or higher for native Live2D rendering.
* WebRTC connections have stable ice-candidate exchange paths via a local signaling server.
* The Cubism 4 SDK library binaries (`.so` files for arm64-v8a) are available and compatible.