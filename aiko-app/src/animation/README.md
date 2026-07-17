# Aiko Live2D Autonomous Expression Pipeline (v5.0)

This directory contains the self-contained physics-informed animation controller module for Aiko. It maps raw neuromodulator states to realistic physical parameters and layers procedural idle actions dynamically.

## 📂 Architecture Overview

```
                        [Neuromodulator Stream]
                                   │
                                   ▼
  1. emotionMapper.ts   ──► [Expression Targets] (eyeOpenness, browTension, etc.)
                                   │
                                   ▼
  2. springSmoother.ts  ──► [Spring Easing Layer] (Critically Damped Spring Physics)
                                   │  (Blended with procedural animations)
                                   ▼
  3. idleLayer.ts       ──► [Procedural Idle Layer] (Breathing, Saccades, random blinks)
                                   │
                                   ▼
  4. paramBinder.ts     ──► [Parameter Binder] (Clamps and sets core parameter values)
                                   │
                                   ▼
  5. useLive2DExpression.ts ◄──► [React Hook API Wrapper]
```

---

## ⚙️ Tuning Guide

You can easily adjust Aiko's animations by tweaking the settings below without rebuilding the core logic:

### 1. Spring Stiffness & Damping Constants (`useLive2DExpression.ts`)
Stiffness is governed by the angular frequency $\omega$ in `springSmoother.ts`. Higher stiffness values ease values faster; lower values add inertia:

* **Head rotation (`headTiltX`, `headTiltY`, `headTiltZ`):** Set to `5.5` - `6.0`. Creating natural head inertia and matching human eye-look delay.
* **Eyes & Mouth (`eyeOpenness`, `mouthOpen`):** Set to `18.0`. Eyes and mouth open/close immediately, simulating instant reflex.
* **Body Sway (`bodySway`):** Set to `4.0`. Slow, heavy somatic sway.
* **Blushing (`blush`):** Set to `8.0`. Natural warmth expansion rate.

To override these in a specific component, pass `stiffnessOverrides` in options:
```typescript
useLive2DExpression(modelRef, chemistry, {
  stiffnessOverrides: {
    headTiltX: 8.0, // makes head turn snappier
  }
});
```

### 2. Neuromodulator Curve Coefficients (`emotionMapper.ts`)
Each neuromodulator maps to expressions via documented mathematical formulas:

* **Eye dilation (Surprise / Daze):**
  $$\text{Dilation} = 1.0 - (\text{melatonin} \times 0.3) + (\text{adrenaline} \times 0.15) + (\text{cortisol} \times 0.08)$$
* **Brow tilt (Worry vs Anger):**
  $$\text{Brow} = (\text{cortisol} \times 0.5) - (\text{adrenaline} \times 0.4 \times (1.0 - \text{serotonin}))$$
* **Cheek Blush (Flustering):**
  $$\text{Blush} = (\text{oxytocin} \times 0.65) + (\text{dopamine} \times \text{arousal} \times 0.35)$$

---

## 🛠️ Developer Integration Example

```tsx
import { useRef } from 'react';
import { useLive2DExpression } from './animation/useLive2DExpression';

export function MyAvatar({ chemistry, isTalking, amplitude }) {
  const modelRef = useRef<any>(null);

  // Bind the pipeline to the Live2D model instance!
  const { triggerDiscreteExpression, debugState } = useLive2DExpression(
    modelRef, 
    chemistry,
    { isTalking, mouthAmplitude: amplitude }
  );

  // Trigger transient override animation on chat alerts
  const handleSurprised = () => {
    triggerDiscreteExpression('shock', { eyeOpenness: 0.25, browTension: 0.6 }, 1200);
  };

  return (
    <div>
      <canvas ref={modelRef} />
      {/* Expose debug state inside visualizer */}
      <pre>{JSON.stringify(debugState.currentSprings, null, 2)}</pre>
    </div>
  );
}
```
