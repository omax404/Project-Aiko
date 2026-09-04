/**
 * aiko-app/src/animation/expressionBlender.ts
 * AAA Expression & Emotion Layer Blender with smooth 350-500ms cross-fade transitions.
 * Combines eyebrows + eyes + mouth + cheek blush + custom overlay masks.
 */

export interface ExpressionPreset {
  name: string;
  eyeOpenness: number;    // 0.0 to 1.2
  browTension: number;    // -1.0 (lowered/angry) to 1.0 (raised/worried)
  mouthCurve: number;     // -1.0 (sad frown) to 1.0 (happy smile)
  mouthOpen: number;      // 0.0 to 1.0
  blush: number;          // 0.0 to 1.0 (cheeks)
  headTiltX: number;      // -1.0 to 1.0
  headTiltY: number;      // -1.0 to 1.0
  headTiltZ: number;      // -1.0 to 1.0
  darkFace?: number;      // 0.0 to 1.0 (gloom overlay)
  cryTears?: number;      // 0.0 to 1.0 (teardrop overlay)
  eyeSmile?: number;      // 0.0 to 1.0
}

export const DEFAULT_EXPRESSION_PRESET: ExpressionPreset = {
  name: 'neutral',
  eyeOpenness: 0.95,
  browTension: 0.0,
  mouthCurve: 0.1,
  mouthOpen: 0.0,
  blush: 0.0,
  headTiltX: 0.0,
  headTiltY: 0.0,
  headTiltZ: 0.0,
};

export const EXPRESSION_PRESETS: Record<string, ExpressionPreset> = {
  neutral: DEFAULT_EXPRESSION_PRESET,

  happy: {
    name: 'happy',
    eyeOpenness: 0.9,
    browTension: 0.25,
    mouthCurve: 0.85,
    mouthOpen: 0.05,
    blush: 0.2,
    headTiltX: 0.1,
    headTiltY: 0.1,
    headTiltZ: 0.15,
    eyeSmile: 0.7,
  },

  shy: {
    name: 'shy',
    eyeOpenness: 0.75,
    browTension: 0.35,
    mouthCurve: 0.3,
    mouthOpen: 0.0,
    blush: 0.85,
    headTiltX: 0.2,
    headTiltY: -0.25,
    headTiltZ: -0.2,
    eyeSmile: 0.3,
  },

  flirty: {
    name: 'flirty',
    eyeOpenness: 0.82,
    browTension: 0.15,
    mouthCurve: 0.65,
    mouthOpen: 0.02,
    blush: 0.45,
    headTiltX: 0.15,
    headTiltY: 0.08,
    headTiltZ: 0.28,
    eyeSmile: 0.5,
  },

  sad: {
    name: 'sad',
    eyeOpenness: 0.7,
    browTension: -0.4,
    mouthCurve: -0.65,
    mouthOpen: 0.0,
    blush: 0.0,
    headTiltX: 0.0,
    headTiltY: -0.3,
    headTiltZ: -0.1,
    cryTears: 0.3,
  },

  surprised: {
    name: 'surprised',
    eyeOpenness: 1.25,
    browTension: 0.7,
    mouthCurve: 0.1,
    mouthOpen: 0.45,
    blush: 0.1,
    headTiltX: 0.0,
    headTiltY: 0.2,
    headTiltZ: 0.0,
  },

  sleepy: {
    name: 'sleepy',
    eyeOpenness: 0.35,
    browTension: -0.1,
    mouthCurve: 0.05,
    mouthOpen: 0.0,
    blush: 0.1,
    headTiltX: 0.0,
    headTiltY: -0.18,
    headTiltZ: 0.1,
  },

  pouty: {
    name: 'pouty',
    eyeOpenness: 0.88,
    browTension: -0.5,
    mouthCurve: -0.4,
    mouthOpen: 0.0,
    blush: 0.3,
    headTiltX: -0.15,
    headTiltY: 0.12,
    headTiltZ: -0.15,
    darkFace: 0.2,
  }
};

export class ExpressionBlender {
  private currentPreset: ExpressionPreset = DEFAULT_EXPRESSION_PRESET;
  private targetPreset: ExpressionPreset = DEFAULT_EXPRESSION_PRESET;
  
  private blendProgress: number = 1.0;
  private blendDuration: number = 0.4; // 400ms cross-fade transition
  private intensity: number = 1.0;

  public setExpression(name: string, intensity: number = 1.0, durationMs: number = 400): void {
    const preset = EXPRESSION_PRESETS[name.toLowerCase()] ?? DEFAULT_EXPRESSION_PRESET;
    if (this.targetPreset.name === preset.name && this.intensity === intensity) return;

    this.currentPreset = this.getBlendedPreset();
    this.targetPreset = preset;
    this.intensity = Math.max(0.0, Math.min(1.0, intensity));
    this.blendDuration = Math.max(0.1, durationMs / 1000.0);
    this.blendProgress = 0.0;
  }

  public update(dt: number): ExpressionPreset {
    if (this.blendProgress < 1.0) {
      this.blendProgress = Math.min(1.0, this.blendProgress + dt / this.blendDuration);
    }
    return this.getBlendedPreset();
  }

  public getBlendedPreset(): ExpressionPreset {
    // Cubic bezier ease-in-out curve: t^2 * (3 - 2t)
    const t = this.blendProgress;
    const ease = t * t * (3 - 2 * t);
    
    const cur = this.currentPreset;
    const tgt = this.targetPreset;
    const k = this.intensity;

    const lerp = (a: number, b: number) => a + (b * k - a) * ease;

    return {
      name: tgt.name,
      eyeOpenness: lerp(cur.eyeOpenness, tgt.eyeOpenness),
      browTension: lerp(cur.browTension, tgt.browTension),
      mouthCurve: lerp(cur.mouthCurve, tgt.mouthCurve),
      mouthOpen: lerp(cur.mouthOpen, tgt.mouthOpen),
      blush: lerp(cur.blush, tgt.blush),
      headTiltX: lerp(cur.headTiltX, tgt.headTiltX),
      headTiltY: lerp(cur.headTiltY, tgt.headTiltY),
      headTiltZ: lerp(cur.headTiltZ, tgt.headTiltZ),
      darkFace: lerp(cur.darkFace || 0, tgt.darkFace || 0),
      cryTears: lerp(cur.cryTears || 0, tgt.cryTears || 0),
      eyeSmile: lerp(cur.eyeSmile || 0, tgt.eyeSmile || 0),
    };
  }
}
