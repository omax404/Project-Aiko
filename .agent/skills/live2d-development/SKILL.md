---
name: live2d-development
description: Implements and optimizes Live2D character models with advanced animations, expressions, and lip-syncing. Use when working with Live2D models, pixi-live2d-display, or connecting emotional states to character parameters.
---

# Live2D Development Skill

This skill provides the knowledge to integrate and control Live2D characters within the Aiko framework using the `pixi-live2d-display` library.

## When to use this skill
- Implementing a new Live2D model.
- Mapping emotional chemicals (Dopamine, Serotonin, etc.) to Live2D expressions.
- Debugging lip-sync issues or motion looping.
- Optimizing model loading and anchor positioning.

## Core Implementation Patterns

### 1. Basic Setup (PIXI Integration)
```javascript
import { Live2DModel } from 'pixi-live2d-display';
import * as PIXI from 'pixi.js';

// Mandatory: Expose PIXI to window for the library
window.PIXI = PIXI;

// Load model
const model = await Live2DModel.from('path/to/model3.json');
app.stage.addChild(model);
```

### 2. Expression & Motion Control
- **Motions:** Represent broad animations (e.g., 'Idle', 'TapBody').
- **Expressions:** Represent static facial states (e.g., 'Happy', 'Angry').

```javascript
// Start a motion by group name
await model.motion('Idle');

// Set a specific expression by index
await model.expression(3); 
```

### 3. Real-time Parameter Manipulation
Use this for **Embodied Cognition** mapping (e.g., breathing, blushing, or micro-expressions based on Adrenaline).

```javascript
const coreModel = model.internalModel.coreModel;
const mouthIndex = coreModel.getParameterIndex('ParamMouthOpenY');
const eyeSmileIndex = coreModel.getParameterIndex('ParamEyeLSmile');

// Update values in the ticker loop
coreModel.setParameterValueByIndex(mouthIndex, 0.8); // Open mouth
```

## Mapping Emotions to Parameters
Follow this standard mapping for Aiko's chemicals:

| Chemical | Live2D Parameter Goal | Expected Behavior |
| :--- | :--- | :--- |
| **Dopamine** | `ParamEyeLSmile`, `ParamMouthForm` | Smiling eyes, curved mouth. |
| **Serotonin** | `ParamEyeLOpen` (relaxed) | Half-lidded, calm gaze. |
| **Cortisol** | `ParamBrowLY`, `ParamBrowRY` | Lowered brows, narrowed eyes (stress). |
| **Adrenaline** | `ParamEyeLOpen` (wide), `ParamCheek` | Wide eyes, blush/flush. |

## Troubleshooting
- **Looping Expressions:** Caused by Idle Motion auto-play. Accept as "lively" or stop the motion manager if static control is needed.
- **Lip Sync Visibility:** Check `ParamMouthOpenY` index. Ensure values reach 1.0. Some models require `ParamMouthForm` to be modified simultaneously for a visible effect.
- **Centering:** Use `model.anchor.set(0.5, 0.5)` and calculate coordinates based on the parent container dimensions.

## Resources
- [See README_LIVE2D.md for advanced debugging](resources/README_LIVE2D.md)
