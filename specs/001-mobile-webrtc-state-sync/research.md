# Research: Mobile WebRTC Data Sync & Custom Rendering

## Findings

### WebRTC Data Channels in aiortc
- The Python package `aiortc` implements RTCPeerConnection and allows listening for `datachannel` events.
- To push unsolicited backend messages down the channel (e.g. `biological_sync` events), the backend must keep references to all open datachannels.
- Datachannels must be monitored for disconnect/close events to avoid memory leaks.

### Native Live2D Cubism SDK on Android
- Current implementation uses a WebView calling WebGL via PixiJS. This induces rendering lag and high CPU/GPU overhead.
- The Live2D Cubism Native SDK uses GLES2.0 / GLES3.0 directly for drawing.
- Standard integration requires:
  1. Loading the native C++ library (`libLive2DCubismCore.so`).
  2. Subclassing `GLSurfaceView.Renderer` to handle `onSurfaceCreated`, `onSurfaceChanged`, and `onDrawFrame`.
  3. Translating screen gestures into model coordinate spaces for interaction tracking.

### Zustand Selectors & React Performance
- Direct selectors like `const state = useNeuralStore()` cause the containing component to re-render whenever *any* store property changes (such as typing indicators or heartbeat counters).
- Refactoring to `const { dopamine } = useNeuralStore(useShallow(state => ({ dopamine: state.dopamine })))` prevents redundant re-renders.
