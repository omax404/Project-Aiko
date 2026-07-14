# Data Model & State Design

## Backend Data Flows

### WebRTC Connection Registry
```python
# In core/api/broadcast.py
webrtc_channels = set() # Set[RTCDataChannel]
```

## Mobile State Model

### StateFlows in ChatRepository.kt
- `_currentEmotion`: StateFlow<EmotionState> representing current dopamine, serotonin, etc.
- `_currentAmplitude`: StateFlow<Float> representing the last voice amplitude envelope value.

## Frontend Selector Refactoring
- All dashboard telemetry widgets will selectively extract their state slice using Zustand `useShallow` checks.
