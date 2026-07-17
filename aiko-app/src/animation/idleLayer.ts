/**
 * Procedural idle animation layer (breathing, blinks, gaze shifts, sways, tears, jitters, wobbles).
 * Blends under the emotion-driven spring variables.
 */
export interface IdleOutputs {
  eyeLOpenOffset: number; // multiplier (usually 1.0, drops to 0.0 during blinks)
  eyeROpenOffset: number;
  eyeBallX: number;       // looking X offset (-0.3 to 0.3)
  eyeBallY: number;       // looking Y offset (-0.2 to 0.2)
  angleXOffset: number;   // micro head drift X (-1.5 to 1.5 degrees)
  angleYOffset: number;   // micro head drift Y (-1.5 to 1.5 degrees)
  angleZOffset: number;   // micro head drift Z (-1.5 to 1.5 degrees)
  breathOffset: number;   // 0.0 to 1.0 (sine breathing wave)
  
  // Custom model outputs
  jitterVal: number;      // High frequency panic jitter
  tearLVal: number;       // Left teardrop pulse
  tearRVal: number;       // Right teardrop pulse
  bobaWobble: number;     // Dynamic wobble reacting to speech and excitement
}

export class IdleLayer {
  private time: number = 0;

  // Blinking State Machine
  private blinkTimer: number = 0;
  private nextBlinkTime: number = 3.0;
  private isBlinking: boolean = false;
  private blinkDuration: number = 0.15; // 150ms duration
  private blinkProgress: number = 0;

  // Gaze Saccade parameters (micro eye jumps)
  private saccadeTimer: number = 0;
  private nextSaccadeTime: number = 2.0;
  private targetGazeX: number = 0;
  private targetGazeY: number = 0;
  private currentGazeX: number = 0;
  private currentGazeY: number = 0;

  // Head drift time offsets (randomized starting points to prevent phase sync)
  private driftTimeX: number = Math.random() * 50;
  private driftTimeY: number = Math.random() * 50;
  private driftTimeZ: number = Math.random() * 50;

  // Procedural physics phases
  private jitterPhase: number = 0;
  private tearPhase: number = 0;
  private wobblePhase: number = 0;

  /**
   * Updates the procedural idle layers.
   * @param dt Delta time in seconds.
   * @param targetBlinkInterval Recommended blink interval from the emotion mapper.
   * @param breathDepth Amplitude modifier for breathing.
   * @param cortisol Stress chemical.
   * @param adrenaline Excitement chemical.
   * @param dopamine Pleasure chemical.
   * @param mouthAmplitude Speech amplitude.
   */
  public update(
    dt: number,
    targetBlinkInterval: number,
    breathDepth: number,
    cortisol: number,
    adrenaline: number,
    dopamine: number,
    mouthAmplitude: number
  ): IdleOutputs {
    this.time += dt;

    // 1. Blinking State Machine
    let eyeOpenMultiplier = 1.0;
    this.blinkTimer += dt;
    if (!this.isBlinking) {
      if (this.blinkTimer >= this.nextBlinkTime) {
        this.isBlinking = true;
        this.blinkProgress = 0;
      }
    } else {
      this.blinkProgress += dt;
      const progressRatio = this.blinkProgress / this.blinkDuration;
      if (progressRatio >= 1.0) {
        this.isBlinking = false;
        this.blinkTimer = 0;
        this.nextBlinkTime = targetBlinkInterval * (0.65 + Math.random() * 0.7);
      } else {
        eyeOpenMultiplier = Math.abs(progressRatio - 0.5) * 2.0;
      }
    }

    // 2. Gaze Saccadic Jumps
    this.saccadeTimer += dt;
    if (this.saccadeTimer >= this.nextSaccadeTime) {
      this.saccadeTimer = 0;
      this.nextSaccadeTime = 0.8 + Math.random() * 2.2;
      if (Math.random() < 0.85) {
        this.targetGazeX = 0;
        this.targetGazeY = 0;
      } else {
        this.targetGazeX = (Math.random() - 0.5) * 0.38;
        this.targetGazeY = (Math.random() - 0.5) * 0.22;
      }
    }
    this.currentGazeX += (this.targetGazeX - this.currentGazeX) * 11.0 * dt;
    this.currentGazeY += (this.targetGazeY - this.currentGazeY) * 11.0 * dt;

    // 3. Head micro sways (overlapping sine waves with prime frequencies)
    this.driftTimeX += dt;
    this.driftTimeY += dt;
    this.driftTimeZ += dt;

    const angleXOffset = (
      Math.sin(this.driftTimeX * 0.65) * 1.0 +
      Math.sin(this.driftTimeX * 1.45) * 0.45 +
      Math.sin(this.driftTimeX * 0.22) * 0.65
    );

    const angleYOffset = (
      Math.cos(this.driftTimeY * 0.75) * 0.95 +
      Math.sin(this.driftTimeY * 1.25) * 0.38 +
      Math.cos(this.driftTimeY * 0.28) * 0.5
    );

    const angleZOffset = (
      Math.sin(this.driftTimeZ * 0.55) * 0.85 +
      Math.cos(this.driftTimeZ * 1.35) * 0.25
    );

    // 4. Breathing Wave (slow, asymmetric breathing wave)
    const breathFrequency = 1.0 + (breathDepth - 1.0) * 0.25;
    const rawCycle = Math.sin(this.time * Math.PI * 0.48 * breathFrequency);
    const shapedBreath = Math.pow(Math.max(0, rawCycle), 1.3) - Math.pow(Math.max(0, -rawCycle), 0.9);
    const breathOffset = (shapedBreath + 1.0) * 0.5 * breathDepth;

    // 5. Jitter/Panic feedback
    let jitterVal = 0;
    if (cortisol > 0.6 || adrenaline > 0.7) {
      this.jitterPhase += dt * 25.0;
      jitterVal = Math.sin(this.jitterPhase) * 0.15 * Math.max(cortisol, adrenaline);
    }

    // 6. Crying Teardrop feedback
    let tearLVal = 0;
    let tearRVal = 0;
    if (cortisol > 0.5 && dopamine < 0.45) {
      this.tearPhase += dt * (0.8 + cortisol * 1.2);
      tearLVal = (Math.sin(this.tearPhase) * 0.5 + 0.5) * cortisol;
      tearRVal = (Math.cos(this.tearPhase * 1.3) * 0.5 + 0.5) * cortisol;
    }

    // 7. Dynamic somatic wobble (driven by speech amplitude and excitement)
    this.wobblePhase += dt * (8.0 + adrenaline * 6.0);
    const wobbleAmp = (mouthAmplitude * 0.15) + (adrenaline * 0.08);
    const bobaWobble = Math.sin(this.wobblePhase) * wobbleAmp;

    return {
      eyeLOpenOffset: eyeOpenMultiplier,
      eyeROpenOffset: eyeOpenMultiplier,
      eyeBallX: this.currentGazeX,
      eyeBallY: this.currentGazeY,
      angleXOffset,
      angleYOffset,
      angleZOffset,
      breathOffset,
      
      // Custom outputs
      jitterVal,
      tearLVal,
      tearRVal,
      bobaWobble
    };
  }
}
