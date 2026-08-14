/**
 * aiko-app/src/animation/idleLayer.ts
 * AAA Procedural Idle & Breathing Layer.
 * Calculates procedural breathing, micro head sways, randomized blinks & double-blinks,
 * 1/f micro-jitters, and saccadic gaze drift.
 */

export interface IdleOutputs {
  eyeLOpenOffset: number; // 0.0 during blink, 1.0 open
  eyeROpenOffset: number;
  eyeBallX: number;       // Saccade eye offset
  eyeBallY: number;
  angleXOffset: number;   // Micro head sway X
  angleYOffset: number;   // Micro head sway Y
  angleZOffset: number;   // Micro head sway Z
  bodyXOffset: number;    // Micro weight shift X
  bodyYOffset: number;    // Micro weight shift Y
  breathOffset: number;   // 0.0 to 1.0 (breathing wave)
  
  // Model feature overlays
  jitterVal: number;
  tearLVal: number;
  tearRVal: number;
  bobaWobble: number;
}

export class IdleLayer {
  private time: number = 0;

  // Breathing State
  private breathPhase: number = Math.random() * Math.PI * 2;
  private breathCycleDuration: number = 4.2; // ~4-5 second cycle

  // Head Sway & Weight Shift State
  private swayTimer: number = 0;
  private nextSwayTime: number = 6.0;
  private targetSwayX: number = 0;
  private targetSwayY: number = 0;
  private targetSwayZ: number = 0;
  private currentSwayX: number = 0;
  private currentSwayY: number = 0;
  private currentSwayZ: number = 0;

  // Blinking State Machine
  private blinkTimer: number = 0;
  private nextBlinkTime: number = 3.2;
  private isBlinking: boolean = false;
  private isDoubleBlink: boolean = false;
  private blinkDuration: number = 0.14; // 140ms
  private blinkProgress: number = 0;

  // Gaze Saccade parameters
  private saccadeTimer: number = 0;
  private nextSaccadeTime: number = 2.4;
  private targetGazeX: number = 0;
  private targetGazeY: number = 0;
  private currentGazeX: number = 0;
  private currentGazeY: number = 0;

  // Noise phase offsets
  private noisePhase: number = Math.random() * 100;

  public update(
    dt: number,
    targetBlinkInterval: number = 3.5,
    breathDepth: number = 1.0,
    cortisol: number = 0.2,
    adrenaline: number = 0.1,
    dopamine: number = 0.5,
    mouthAmplitude: number = 0.0
  ): IdleOutputs {
    this.time += dt;
    const adrenalinePulse = adrenaline * 0.1;

    // 1. Continuous Breathing Motion (~4-5s randomized cycle)
    // Slightly modulate frequency so breathing doesn't feel metronomic
    const breathFreq = (2 * Math.PI) / (this.breathCycleDuration + Math.sin(this.time * 0.3) * 0.4);
    this.breathPhase += breathFreq * dt;
    const rawBreath = Math.sin(this.breathPhase);
    // Smooth pulse (0.0 to 1.0)
    const breathOffset = (rawBreath * 0.5 + 0.5) * breathDepth;

    // 2. Micro Head Sway & Weight Shift (every 6-10 seconds with Cubic Bezier easing)
    this.swayTimer += dt;
    if (this.swayTimer >= this.nextSwayTime) {
      this.swayTimer = 0;
      this.nextSwayTime = 6.0 + Math.random() * 4.0; // 6-10s interval
      
      // Random subtle targets
      this.targetSwayX = (Math.random() - 0.5) * 2.2; // degrees
      this.targetSwayY = (Math.random() - 0.5) * 1.8;
      this.targetSwayZ = (Math.random() - 0.5) * 1.5;
    }

    // Cubic Bezier interpolation towards sway targets (smooth ease-in-out)
    const swayT = Math.min(1.0, dt * 1.8);
    const easeSway = swayT * swayT * (3 - 2 * swayT);
    this.currentSwayX += (this.targetSwayX - this.currentSwayX) * easeSway;
    this.currentSwayY += (this.targetSwayY - this.currentSwayY) * easeSway;
    this.currentSwayZ += (this.targetSwayZ - this.currentSwayZ) * easeSway;

    // 3. Natural Blinking (single & double blinks, variable speed)
    let eyeOpenMultiplier = 1.0;
    this.blinkTimer += dt;

    if (!this.isBlinking) {
      if (this.blinkTimer >= this.nextBlinkTime) {
        this.isBlinking = true;
        this.blinkProgress = 0;
        // 20% chance of double blink for realism
        this.isDoubleBlink = Math.random() < 0.20;
        // Slightly vary blink duration (120ms to 170ms)
        this.blinkDuration = 0.12 + Math.random() * 0.05;
      }
    } else {
      this.blinkProgress += dt;
      const effectiveDuration = this.isDoubleBlink ? this.blinkDuration * 1.8 : this.blinkDuration;
      const progressRatio = this.blinkProgress / effectiveDuration;

      if (progressRatio >= 1.0) {
        this.isBlinking = false;
        this.blinkTimer = 0;
        // Next blink in 2-6s (randomized interval modulated by targetBlinkInterval & adrenaline)
        this.nextBlinkTime = Math.max(1.5, targetBlinkInterval * (0.6 + Math.random() * 0.8) - adrenalinePulse);
      } else {
        if (this.isDoubleBlink) {
          // Two dip cycles
          eyeOpenMultiplier = Math.abs(Math.sin(progressRatio * Math.PI * 2));
        } else {
          // Single smooth blink envelope
          eyeOpenMultiplier = Math.abs(progressRatio - 0.5) * 2.0;
        }
      }
    }

    // 4. Micro Gaze Saccades
    this.saccadeTimer += dt;
    if (this.saccadeTimer >= this.nextSaccadeTime) {
      this.saccadeTimer = 0;
      this.nextSaccadeTime = 1.5 + Math.random() * 3.0;
      if (Math.random() < 0.8) {
        this.targetGazeX = 0;
        this.targetGazeY = 0;
      } else {
        this.targetGazeX = (Math.random() - 0.5) * 0.25;
        this.targetGazeY = (Math.random() - 0.5) * 0.18;
      }
    }
    this.currentGazeX += (this.targetGazeX - this.currentGazeX) * dt * 8.0;
    this.currentGazeY += (this.targetGazeY - this.currentGazeY) * dt * 8.0;

    // 5. Subtle 1/f noise (very low amplitude) so character is never robotic or frozen
    this.noisePhase += dt * 2.5;
    const microNoiseX = Math.sin(this.noisePhase * 1.1) * 0.12;
    const microNoiseY = Math.cos(this.noisePhase * 0.8) * 0.10;

    // Secondary feature outputs
    const bobaWobble = Math.sin(this.time * 4.0) * (dopamine * 0.15 + mouthAmplitude * 0.2);
    const jitterVal = cortisol > 0.65 ? Math.sin(this.time * 25.0) * 0.15 : 0;
    const tearVal = cortisol > 0.7 ? Math.sin(this.time * 2.0) * 0.5 + 0.5 : 0;

    return {
      eyeLOpenOffset: eyeOpenMultiplier,
      eyeROpenOffset: eyeOpenMultiplier,
      eyeBallX: this.currentGazeX,
      eyeBallY: this.currentGazeY,
      angleXOffset: this.currentSwayX + microNoiseX,
      angleYOffset: this.currentSwayY + (rawBreath * 0.8) + microNoiseY,
      angleZOffset: this.currentSwayZ + Math.sin(this.time * 0.7) * 0.2,
      bodyXOffset: this.currentSwayX * 0.35,
      bodyYOffset: rawBreath * 0.5,
      breathOffset,
      jitterVal,
      tearLVal: tearVal,
      tearRVal: tearVal,
      bobaWobble,
    };
  }
}
