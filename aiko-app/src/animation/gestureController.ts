/**
 * aiko-app/src/animation/gestureController.ts
 * AAA One-Shot Gesture & Reaction System for Live2D Characters.
 * Allows triggering discrete gestures (greet, handToFace, nod, surprisedJolt, goodnight)
 * that layer over idle/physics and smoothly blend back without snapping.
 */

export interface GestureDefinition {
  name: string;
  duration: number; // Duration in seconds
  cooldown: number; // Cooldown in seconds (20-30s per requirement)
  paramOffsets: (progress: number) => Record<string, number>;
}

// Ease curves for smooth gesture envelopes
function easeInOutQuad(t: number): number {
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
}

function easeOutBack(t: number): number {
  const c1 = 1.70158;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
}

export const GESTURE_PRESETS: Record<string, GestureDefinition> = {
  greet: {
    name: 'greet',
    duration: 1.4,
    cooldown: 20,
    paramOffsets: (p: number) => {
      // Warm head tilt + subtle upward nod
      const envelope = Math.sin(p * Math.PI);
      return {
        ParamAngleZ: 8.0 * envelope,
        ParamAngleY: 5.0 * Math.sin(p * Math.PI * 2) * envelope,
        ParamBodyAngleZ: 3.5 * envelope,
        ParamMouthForm: 0.6 * envelope,
        ParamEyeLSmile: 0.8 * envelope,
        ParamEyeRSmile: 0.8 * envelope,
      };
    }
  },

  handToFace: {
    name: 'handToFace',
    duration: 1.8,
    cooldown: 25,
    paramOffsets: (p: number) => {
      // Shy head tilt down-right + heavy blush + eye lowering
      const envelope = easeInOutQuad(Math.sin(p * Math.PI));
      return {
        ParamAngleX: 12.0 * envelope,
        ParamAngleY: -14.0 * envelope,
        ParamAngleZ: -6.0 * envelope,
        ParamCheek: 0.85 * envelope,
        Param149: 0.9 * envelope, // Custom blush overlay
        ParamEyeLOpen: -0.3 * envelope,
        ParamEyeROpen: -0.3 * envelope,
        ParamBrowLY: -0.3 * envelope,
        ParamBrowRY: -0.3 * envelope,
      };
    }
  },

  nod: {
    name: 'nod',
    duration: 0.9,
    cooldown: 10,
    paramOffsets: (p: number) => {
      // Gentle double agreement nod
      const doubleNod = Math.sin(p * Math.PI * 3);
      const envelope = Math.sin(p * Math.PI);
      return {
        ParamAngleY: -8.0 * doubleNod * envelope,
        ParamBodyAngleY: -2.5 * doubleNod * envelope,
      };
    }
  },

  surprisedJolt: {
    name: 'surprisedJolt',
    duration: 1.1,
    cooldown: 15,
    paramOffsets: (p: number) => {
      // Fast recoil up with overshoot, then slow settle
      const envelope = easeOutBack(Math.min(1.0, p * 2.0)) * Math.max(0, 1.0 - p);
      return {
        ParamAngleY: 15.0 * envelope,
        ParamAngleX: -4.0 * envelope,
        ParamBodyAngleY: 6.0 * envelope,
        ParamEyeLOpen: 0.35 * envelope,
        ParamEyeROpen: 0.35 * envelope,
        Param132: 0.6 * envelope, // Flustered/Panic jitter trigger
      };
    }
  },

  goodnight: {
    name: 'goodnight',
    duration: 2.2,
    cooldown: 30,
    paramOffsets: (p: number) => {
      // Slow drooping eyes + soft tilt down
      const envelope = Math.sin(p * Math.PI);
      return {
        ParamAngleY: -10.0 * envelope,
        ParamAngleZ: 5.0 * envelope,
        ParamEyeLOpen: -0.6 * envelope,
        ParamEyeROpen: -0.6 * envelope,
        ParamMouthForm: 0.4 * envelope,
        ParamBodyAngleY: -4.0 * envelope,
      };
    }
  }
};

export class GestureController {
  private activeGesture: {
    preset: GestureDefinition;
    elapsed: number;
  } | null = null;

  private cooldownTimers: Map<string, number> = new Map();

  public update(dt: number): Record<string, number> {
    // Tick cooldown timers
    for (const [key, time] of this.cooldownTimers.entries()) {
      const remaining = time - dt;
      if (remaining <= 0) {
        this.cooldownTimers.delete(key);
      } else {
        this.cooldownTimers.set(key, remaining);
      }
    }

    if (!this.activeGesture) return {};

    this.activeGesture.elapsed += dt;
    const { preset, elapsed } = this.activeGesture;
    const progress = Math.min(1.0, elapsed / preset.duration);

    if (progress >= 1.0) {
      // Finished
      this.activeGesture = null;
      return {};
    }

    return preset.paramOffsets(progress);
  }

  public playGesture(name: string): boolean {
    const preset = GESTURE_PRESETS[name];
    if (!preset) {
      console.warn(`[GestureController] Unknown gesture: ${name}`);
      return false;
    }

    // Check rate limit cooldown
    if (this.cooldownTimers.has(name)) {
      console.log(`[GestureController] Gesture ${name} is on cooldown (${this.cooldownTimers.get(name)?.toFixed(1)}s remaining).`);
      return false;
    }

    // Trigger gesture
    this.activeGesture = { preset, elapsed: 0 };
    this.cooldownTimers.set(name, preset.cooldown);
    console.log(`[GestureController] Playing gesture: ${name}`);
    return true;
  }

  public isPlaying(): boolean {
    return this.activeGesture !== null;
  }
}
