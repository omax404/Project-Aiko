/**
 * Maps raw neuromodulator states (dopamine, serotonin, cortisol, etc.) to intermediate expression targets.
 */
export interface NeuromodulatorState {
  dopamine: number;
  serotonin: number;
  cortisol: number;
  adrenaline: number;
  oxytocin?: number;
  melatonin?: number;
  // Fallbacks for optional fields
  norepinephrine?: number;
  arousal?: number;
  valence?: number;
}

export interface ExpressionTargets {
  eyeOpenness: number;    // 0.0 (closed) to 1.2 (wide)
  browTension: number;    // -1.0 (lowered/angry) to 1.0 (raised/worried)
  mouthCurve: number;     // -1.0 (sad frown) to 1.0 (happy smile)
  mouthOpen: number;      // 0.0 to 1.0 (ambient mouth open)
  headTiltX: number;      // -1.0 to 1.0 (look left/right)
  headTiltY: number;      // -1.0 to 1.0 (look up/down)
  headTiltZ: number;      // -1.0 to 1.0 (head roll tilt)
  bodySway: number;       // -1.0 to 1.0 (body lean)
  blinkRate: number;      // Duration in seconds between blinks (1.5 to 6.0)
  breathDepth: number;    // 0.4 to 1.5 (amplitude of breathing)
  blush: number;          // 0.0 to 1.0 (blushing cheeks)
}

/**
 * Maps the incoming neuromodulator chemistry state to expression targets.
 * Tuned with linear, sigmoid, and threshold equations for lifelike response.
 */
export function mapEmotionToTargets(state: NeuromodulatorState): ExpressionTargets {
  // Normalize and clamp inputs to [0, 1] range safely
  const dopamine = clamp(state.dopamine, 0, 1);
  const serotonin = clamp(state.serotonin, 0, 1);
  const cortisol = clamp(state.cortisol, 0, 1);
  const adrenaline = clamp(state.adrenaline, 0, 1);
  
  const oxytocin = clamp(state.oxytocin ?? 0.3, 0, 1);
  const melatonin = clamp(state.melatonin ?? 0.1, 0, 1);
  
  // Synthesize arousal and valence from raw chemistry if not directly supplied
  const arousal = clamp(state.arousal ?? (0.3 * dopamine + 0.5 * adrenaline + 0.2 * cortisol), 0, 1);
  const valence = clamp(state.valence ?? (0.4 * serotonin + 0.4 * dopamine - 0.5 * cortisol - 0.3 * adrenaline), -1, 1);

  // 1. Eye Openness
  // Dilation is driven by excitement/stress (adrenaline, cortisol). Sleepiness (melatonin) reduces it.
  const baseEye = 0.95;
  const sleepReduction = melatonin * 0.3;
  const stressDilation = (adrenaline * 0.15) + (cortisol * 0.08);
  const eyeOpenness = clamp(baseEye - sleepReduction + stressDilation, 0.5, 1.2);

  // 2. Brow Tension
  // Worry (cortisol) raises inner brows. Tension/anger (adrenaline + low serotonin) lowers brows.
  const worryOffset = cortisol * 0.5;
  const tensionOffset = adrenaline * 0.4 * (1.0 - serotonin);
  const browTension = clamp(worryOffset - tensionOffset, -1.0, 1.0);

  // 3. Mouth Curve
  // Driven primarily by valence. Serotonin adds a gentle baseline smile. Cortisol pulls it into a frown.
  const mouthCurve = clamp(valence * 0.65 + serotonin * 0.25 - cortisol * 0.3, -1.0, 1.0);

  // 4. Mouth Open (ambient default, speech overrides this)
  // Slight opening on high surprise / high dopamine excitement
  const mouthOpen = (valence > 0.45 && dopamine > 0.75) ? 0.08 : 0.0;

  // 5. Head Tilt X, Y, Z
  // High dopamine + oxytocin -> playful, leaning tilt. Sadness/cortisol -> hanging down.
  const headTiltX = valence * dopamine * 0.15;
  const headTiltY = (dopamine * 0.18) - (cortisol * 0.28); // Leaning down on stress/sadness
  const headTiltZ = oxytocin * dopamine * 0.22; // Warm curious head tilt

  // 6. Body Sway
  const bodySway = valence * serotonin * 0.15;

  // 7. Blink Rate (interval in seconds between blinks)
  // Normal rate is ~4s. High stress/adrenaline -> blinks more frequently (1.8s). Calm -> 5.5s.
  const baseBlinkRate = 4.0;
  const stressFactor = 1.0 - (adrenaline * 0.45) - (cortisol * 0.15);
  const calmFactor = 1.0 + (serotonin * 0.35);
  const blinkRate = clamp(baseBlinkRate * stressFactor * calmFactor, 1.5, 6.0);

  // 8. Breath Depth
  // High arousal/adrenaline -> deeper/faster breathing. Sleepiness -> shallow breathing.
  const breathDepth = clamp(0.85 + (arousal * 0.45) - (melatonin * 0.25), 0.4, 1.4);

  // 9. Blush
  // High affection (oxytocin) or flustered excitement (dopamine + arousal)
  const blush = clamp(oxytocin * 0.65 + (dopamine * arousal * 0.35), 0.0, 1.0);

  return {
    eyeOpenness,
    browTension,
    mouthCurve,
    mouthOpen,
    headTiltX,
    headTiltY,
    headTiltZ,
    bodySway,
    blinkRate,
    breathDepth,
    blush
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}
