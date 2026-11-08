/**
 * aiko-app/src/animation/idleLayer.ts
 * AAA Procedural Idle & Breathing Layer.
 * Calculates multi-harmonic procedural breathing, continuous organic head/body drift,
 * asymmetric biological blinks & double-blinks, conversational speech cadence,
 * and saccadic gaze drift.
 */

export interface IdleOutputs {
  eyeLOpenOffset: number; // 0.0 during blink, 1.0 open
  eyeROpenOffset: number;
  eyeBallX: number;       // Saccade eye offset
  eyeBallY: number;
  angleXOffset: number;   // Smooth head sway X
  angleYOffset: number;   // Smooth head sway Y
  angleZOffset: number;   // Smooth head sway Z
  bodyXOffset: number;    // Smooth weight shift X
  bodyYOffset: number;    // Smooth weight shift Y
  bodyZOffset?: number;   // Smooth body roll Z
  shoulderYOffset?: number; // Shoulder rise with breath
  hipXOffset?: number;      // Subtle counter-balance hip sway
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
  private nextSwayTime: number = 5.0;
  private targetSwayX: number = 0;
  private targetSwayY: number = 0;
  private targetSwayZ: number = 0;
  private currentSwayX: number = 0;
  private currentSwayY: number = 0;
  private currentSwayZ: number = 0;
  private velocitySwayX: number = 0;
  private velocitySwayY: number = 0;
  private velocitySwayZ: number = 0;

  // Blinking State Machine
  private blinkTimer: number = 0;
  private nextBlinkTime: number = 3.2;
  private isBlinking: boolean = false;
  private isDoubleBlink: boolean = false;
  private blinkDuration: number = 0.15; // 150ms
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

  private stepSpring(
    current: number,
    velocity: number,
    target: number,
    omega: number,
    dt: number
  ): [number, number] {
    const x0 = current - target;
    const expTerm = Math.exp(-omega * dt);
    const c = velocity + omega * x0;
    const nextPos = (x0 + c * dt) * expTerm + target;
    const nextVel = (velocity - omega * c * dt) * expTerm;
    return [nextPos, nextVel];
  }

  /**
   * Asymmetric biological blink curve:
   * Eyelid closes rapidly (first 32% of duration) and opens smoothly (remaining 68%).
   */
  private computeSingleBlinkCurve(t: number): number {
    const clamped = Math.max(0, Math.min(1, t));
    const closeSplit = 0.32;
    if (clamped < closeSplit) {
      const p = clamped / closeSplit;
      // Fast cubic ease-in to 0
      return 1.0 - p * p * (3 - 2 * p);
    }
    const p = (clamped - closeSplit) / (1.0 - closeSplit);
    // Smooth ease-out back to 1
    return p * p * (3 - 2 * p);
  }

  public update(
    dt: number,
    targetBlinkInterval: number = 3.5,
    breathDepth: number = 1.0,
    cortisol: number = 0.2,
    adrenaline: number = 0.1,
    dopamine: number = 0.5,
    mouthAmplitude: number = 0.0
  ): IdleOutputs {
    const safeDt = Math.max(0.0001, Math.min(0.05, dt));
    this.time += safeDt;
    const adrenalinePulse = adrenaline * 0.1;

    // 1. Continuous Breathing Motion (~4-5s modulated cycle)
    const breathFreq = (2 * Math.PI) / (this.breathCycleDuration + Math.sin(this.time * 0.27) * 0.35);
    this.breathPhase += breathFreq * safeDt;
    const rawBreath = Math.sin(this.breathPhase);
    // Smooth shaped inhale/exhale wave (0.0 to 1.0)
    const normalizedBreath = rawBreath * 0.5 + 0.5;
    const shapedBreath = normalizedBreath * normalizedBreath * (3 - 2 * normalizedBreath);
    const breathOffset = shapedBreath * breathDepth;

    // 2. Continuous Multi-Harmonic Drift + Critically-Damped Posture Shifts
    this.swayTimer += safeDt;
    if (this.swayTimer >= this.nextSwayTime) {
      this.swayTimer = 0;
      this.nextSwayTime = 4.5 + Math.random() * 3.5;

      this.targetSwayX = (Math.random() - 0.5) * 3.2; // degrees
      this.targetSwayY = (Math.random() - 0.5) * 2.4;
      this.targetSwayZ = (Math.random() - 0.5) * 2.2;
    }

    // Critically damped low-omega spring (omega = 1.8) for velvety posture transitions
    [this.currentSwayX, this.velocitySwayX] = this.stepSpring(
      this.currentSwayX,
      this.velocitySwayX,
      this.targetSwayX,
      1.8,
      safeDt
    );
    [this.currentSwayY, this.velocitySwayY] = this.stepSpring(
      this.currentSwayY,
      this.velocitySwayY,
      this.targetSwayY,
      1.6,
      safeDt
    );
    [this.currentSwayZ, this.velocitySwayZ] = this.stepSpring(
      this.currentSwayZ,
      this.velocitySwayZ,
      this.targetSwayZ,
      1.5,
      safeDt
    );

    // 3. Natural Biological Blinking (asymmetric single & double blinks)
    let eyeOpenMultiplier = 1.0;
    this.blinkTimer += safeDt;

    if (!this.isBlinking) {
      if (this.blinkTimer >= this.nextBlinkTime) {
        this.isBlinking = true;
        this.blinkProgress = 0;
        this.isDoubleBlink = Math.random() < 0.18;
        this.blinkDuration = 0.13 + Math.random() * 0.04;
      }
    } else {
      this.blinkProgress += safeDt;
      const effectiveDuration = this.isDoubleBlink ? this.blinkDuration * 2.1 : this.blinkDuration;
      const progressRatio = this.blinkProgress / effectiveDuration;

      if (progressRatio >= 1.0) {
        this.isBlinking = false;
        this.blinkTimer = 0;
        this.nextBlinkTime = Math.max(
          1.5,
          targetBlinkInterval * (0.65 + Math.random() * 0.75) - adrenalinePulse
        );
      } else if (this.isDoubleBlink) {
        const subProgress = (progressRatio * 2.0) % 1.0;
        eyeOpenMultiplier = this.computeSingleBlinkCurve(subProgress);
      } else {
        eyeOpenMultiplier = this.computeSingleBlinkCurve(progressRatio);
      }
    }

    // 4. Micro Gaze Saccades with smooth exponential damping
    this.saccadeTimer += safeDt;
    if (this.saccadeTimer >= this.nextSaccadeTime) {
      this.saccadeTimer = 0;
      this.nextSaccadeTime = 1.6 + Math.random() * 2.8;
      if (Math.random() < 0.72) {
        this.targetGazeX = 0;
        this.targetGazeY = 0;
      } else {
        this.targetGazeX = (Math.random() - 0.5) * 0.24;
        this.targetGazeY = (Math.random() - 0.5) * 0.16;
      }
    }
    const saccadeBlend = 1.0 - Math.exp(-10.0 * safeDt);
    this.currentGazeX += (this.targetGazeX - this.currentGazeX) * saccadeBlend;
    this.currentGazeY += (this.targetGazeY - this.currentGazeY) * saccadeBlend;

    // 5. Multi-Harmonic Organic Motion + Speech Conversational Cadence
    this.noisePhase += safeDt * 1.4;
    const harmonicX =
      Math.sin(this.noisePhase * 0.9) * 0.85 +
      Math.sin(this.noisePhase * 2.1 + 1.3) * 0.28;
    const harmonicY =
      Math.cos(this.noisePhase * 0.75) * 0.65 +
      Math.sin(this.noisePhase * 1.7 + 0.5) * 0.22;
    const harmonicZ =
      Math.sin(this.noisePhase * 0.55 + 0.8) * 0.95 +
      Math.cos(this.noisePhase * 1.3) * 0.3;

    // Subtle conversational head/body cadence when speaking
    const speechActive = Math.min(1.0, mouthAmplitude * 1.4);
    const speechNodY = speechActive * Math.sin(this.time * 7.5) * 1.6;
    const speechTiltZ = speechActive * Math.cos(this.time * 4.2) * 1.1;
    const speechYawX = speechActive * Math.sin(this.time * 3.1) * 0.9;

    // Secondary feature outputs
    const bobaWobble = Math.sin(this.time * 3.6) * (dopamine * 0.12 + mouthAmplitude * 0.18);
    const jitterVal = cortisol > 0.68 ? Math.sin(this.time * 18.0) * 0.12 : 0;
    const tearVal = cortisol > 0.75 ? Math.sin(this.time * 2.0) * 0.4 + 0.4 : 0;

    const totalAngleX = this.currentSwayX + harmonicX + speechYawX;
    const totalAngleY = this.currentSwayY + rawBreath * 0.95 + harmonicY + speechNodY;
    const totalAngleZ = this.currentSwayZ + harmonicZ + speechTiltZ;

    return {
      eyeLOpenOffset: eyeOpenMultiplier,
      eyeROpenOffset: eyeOpenMultiplier,
      eyeBallX: this.currentGazeX,
      eyeBallY: this.currentGazeY,
      angleXOffset: totalAngleX,
      angleYOffset: totalAngleY,
      angleZOffset: totalAngleZ,
      bodyXOffset: totalAngleX * 0.38,
      bodyYOffset: rawBreath * 0.55 + speechNodY * 0.25,
      bodyZOffset: totalAngleZ * 0.32,
      shoulderYOffset: rawBreath * 0.75,
      hipXOffset: -totalAngleX * 0.2,
      breathOffset,
      jitterVal,
      tearLVal: tearVal,
      tearRVal: tearVal,
      bobaWobble,
    };
  }
}
