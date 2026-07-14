import React, { useEffect, useRef, useState } from 'react';
import { useNeuralStore } from '../store/useNeuralStore';

interface Live2DAvatarProps {
  modelUrl: string;
  isThinking?: boolean;
  isTalking?: boolean;
  emotion?: string;
  width?: number;
  height?: number;
  scale?: number;
  amplitude?: number;
  chemicals?: {
    dopamine: number;
    serotonin: number;
    cortisol: number;
    adrenaline: number;
    oxytocin?: number;
    melatonin?: number;
  };
  offsetX?: number;
  offsetY?: number;
}

export const Live2DAvatar: React.FC<Live2DAvatarProps> = ({
  modelUrl,
  isThinking,
  isTalking,
  emotion = 'neutral',
  width = 400,
  height = 500,
  scale: externalScale = 1.0,
  amplitude = 0,
  chemicals,
  offsetX = 0,
  offsetY = 0
}) => {
  const store = useNeuralStore();
  const currentChemicals = chemicals || store.chemicals;

  const {
    jitterIntensity = 0.4,
    tearIntensity = 1.0,
    leanIntensity = 1.0,
    blushIntensity = 1.0,
    poutIntensity = 1.0,
    bobaIntensity = 1.0,
    oxytocinIntensity = 1.0,
    melatoninIntensity = 1.0
  } = store;

  const scalersRef = useRef({
    jitterIntensity,
    tearIntensity,
    leanIntensity,
    blushIntensity,
    poutIntensity,
    bobaIntensity,
    oxytocinIntensity,
    melatoninIntensity
  });

  useEffect(() => {
    scalersRef.current = {
      jitterIntensity,
      tearIntensity,
      leanIntensity,
      blushIntensity,
      poutIntensity,
      bobaIntensity,
      oxytocinIntensity,
      melatoninIntensity
    };
  }, [
    jitterIntensity,
    tearIntensity,
    leanIntensity,
    blushIntensity,
    poutIntensity,
    bobaIntensity,
    oxytocinIntensity,
    melatoninIntensity
  ]);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const appRef = useRef<any>(null);
  const modelRef = useRef<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  // Animation state refs for the ticker loop
  const animationState = useRef({
    time: 0,
    blinkTimer: 0,
    nextBlink: 2 + Math.random() * 4,
    talkPhase: 0,
    isTalking: false,
  });

  // Keep track of props/store in refs to avoid re-running initialization effect
  const chemicalsRef = useRef(currentChemicals);
  useEffect(() => { chemicalsRef.current = currentChemicals; }, [currentChemicals]);

  const smoothedChemicals = useRef({
    dopamine: 0.5,
    serotonin: 0.5,
    cortisol: 0.0,
    adrenaline: 0.0,
    oxytocin: 0.3,
    melatonin: 0.1,
    // Add smoothed animation parameters
    angleX: 0,
    angleY: 0,
    angleZ: 0,
    bodyAngleX: 0,
    bodyAngleY: 0,
    eyeBallX: 0,
    eyeBallY: 0,
    blush: 0,
    pout: 0
  });

  const amplitudeRef = useRef(amplitude);
  useEffect(() => { amplitudeRef.current = amplitude; }, [amplitude]);

  const emotionRef = useRef(emotion);
  useEffect(() => { emotionRef.current = emotion; }, [emotion]);

  useEffect(() => {
    animationState.current.isTalking = !!isTalking;
  }, [isTalking]);

  useEffect(() => {
    if (!canvasRef.current) return;
    let destroyed = false;

    let handleMouseMove: ((e: MouseEvent) => void) | null = null;
    let handleMouseLeave: (() => void) | null = null;
    let mouseTimeout: ReturnType<typeof setTimeout> | null = null;

    const init = async () => {
      try {
        if (!(window as any).Live2DCubismCore) {
          throw new Error('Live2DCubismCore not loaded. Check live2dcubismcore.min.js in public/live2d/');
        }

        const PIXI = await import('pixi.js');
        (window as any).PIXI = PIXI;
        const { Live2DModel } = await import('pixi-live2d-display/cubism4');
        Live2DModel.registerTicker(PIXI.Ticker);

        if (destroyed) return;

        const app = new PIXI.Application({
          view: canvasRef.current!,
          backgroundAlpha: 0,
          width,
          height,
          autoStart: true,
          resolution: Math.min(window.devicePixelRatio || 1, 2),
          autoDensity: true,
          antialias: true,
        });

        appRef.current = app;

        const model = await Live2DModel.from(modelUrl, {
          idleMotionGroup: 'idle'
        });

        if (destroyed) {
          app.destroy(false);
          return;
        }

        modelRef.current = model;
        model.autoUpdate = false;

        // Improved scaling logic to fill more space
        const calculateScale = () => {
          const modelW = model.internalModel.originalWidth;
          const modelH = model.internalModel.originalHeight;
          
          // Fill 95% of height or width, then multiply by external scale
          const scaleX = (width * 0.95) / modelW;
          const scaleY = (height * 0.95) / modelH;
          return Math.min(scaleX, scaleY) * externalScale;
        };

        const scale = calculateScale();
        model.scale.set(scale);
        model.anchor.set(0.5, 0.5);
        // Position in middle of canvas plus custom alignment offsets
        model.position.set(width / 2 + offsetX, height / 2 + offsetY);

        app.stage.addChild(model);

        // Track dynamic animation phases (e.g. tear flows)
        let tearPhase = 0;
        let jitterPhase = 0;

        // Mouse tracking for cursor follow
        let mouseActive = false;
        const mousePos = { x: width / 2, y: height / 2 };

        handleMouseMove = (e: MouseEvent) => {
          mouseActive = true;
          mousePos.x = e.clientX;
          mousePos.y = e.clientY;

          if (mouseTimeout) clearTimeout(mouseTimeout);
          mouseTimeout = setTimeout(() => {
            mouseActive = false;
          }, 3000);
        };

        handleMouseLeave = () => {
          mouseActive = false;
          if (mouseTimeout) clearTimeout(mouseTimeout);
        };

        window.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseleave', handleMouseLeave);

        // Core unified animation loop
        app.ticker.add(() => {
          if (!modelRef.current) return;
          const delta = app.ticker.elapsedMS / 1000;
          
          // Manually update the model first so motions, expression transitions,
          // and physics run before we add our custom overrides.
          try {
            modelRef.current.update(app.ticker.elapsedMS);
          } catch (_) {}

          const time = app.ticker.lastTime / 1000;
          const state = animationState.current;
          state.time += delta;
          
          const core = modelRef.current.internalModel?.coreModel;
          if (!core) return;

          const chem = chemicalsRef.current;
          const targetChem = chem || { dopamine: 0.5, serotonin: 0.5, cortisol: 0, adrenaline: 0, oxytocin: 0.3, melatonin: 0.1 };
          const curEmotion = emotionRef.current;

          const {
            jitterIntensity,
            tearIntensity,
            leanIntensity,
            blushIntensity,
            poutIntensity,
            bobaIntensity,
            oxytocinIntensity,
            melatoninIntensity
          } = scalersRef.current;

          // 1. Smoothly interpolate (lerp) neuromodulator values to prevent popping/snapping
          const smooth = smoothedChemicals.current;
          const lerp = (current: number, target: number, speed: number) => {
            const f = 1 - Math.exp(-speed * delta);
            return current + (target - current) * f;
          };

          // Use approx. 4.0 speed for natural ~250ms smoothing half-life
          const smoothSpeed = 4.0;
          smooth.dopamine = lerp(smooth.dopamine, targetChem.dopamine, smoothSpeed);
          smooth.serotonin = lerp(smooth.serotonin, targetChem.serotonin, smoothSpeed);
          smooth.cortisol = lerp(smooth.cortisol, targetChem.cortisol, smoothSpeed);
          smooth.adrenaline = lerp(smooth.adrenaline, targetChem.adrenaline, smoothSpeed);
          smooth.oxytocin = lerp(smooth.oxytocin, targetChem.oxytocin ?? 0.3, smoothSpeed);
          smooth.melatonin = lerp(smooth.melatonin, targetChem.melatonin ?? 0.1, smoothSpeed);

          const dopamine = smooth.dopamine;
          const serotonin = smooth.serotonin;
          const cortisol = smooth.cortisol;
          const adrenaline = smooth.adrenaline;
          const oxytocin = smooth.oxytocin;
          const melatonin = smooth.melatonin;

          try {
            const currentIsTalking = state.isTalking;
            const currentAmplitude = amplitudeRef.current;
            
            // 2. Head/body movement (either mouse cursor tracking or slow organic wandering)
            let targetAngleX = 0;
            let targetAngleY = 0;
            let targetBodyAngleX = 0;

            let targetEyeX = 0;
            let targetEyeY = 0;

            if (mouseActive) {
                const centerX = width / 2;
                const centerY = height / 2;
                const dx = (mousePos.x - centerX) / (width / 2);
                const dy = (mousePos.y - centerY) / (height / 2);

                // Live2D Angle ranges: X (-30 to 30), Y (-30 to 30)
                targetAngleX = Math.max(-30, Math.min(30, dx * 30.0));
                targetAngleY = Math.max(-30, Math.min(30, -dy * 30.0)); // Invert Y
                targetBodyAngleX = targetAngleX * 0.5;

                // Eyeball ranges: X (-1 to 1), Y (-1 to 1)
                targetEyeX = Math.max(-1.0, Math.min(1.0, dx * 1.2));
                targetEyeY = Math.max(-1.0, Math.min(1.0, -dy * 1.2));
            } else {
                const wanderSpeed = 0.5;
                targetAngleX = Math.sin(state.time * wanderSpeed) * 5.0 * (1.0 - melatonin);
                targetAngleY = Math.cos(state.time * wanderSpeed * 0.73) * 3.0 * (1.0 - melatonin);
                targetBodyAngleX = targetAngleX * 0.45;

                targetEyeX = 0;
                targetEyeY = 0;
            }

            smooth.angleX = lerp(smooth.angleX, targetAngleX, 3.0);
            smooth.angleY = lerp(smooth.angleY, targetAngleY, 3.0);
            smooth.bodyAngleX = lerp(smooth.bodyAngleX, targetBodyAngleX, 3.0);

            core.setParameterValueById('ParamAngleX', smooth.angleX);
            core.setParameterValueById('ParamAngleY', smooth.angleY);
            core.setParameterValueById('ParamBodyAngleX', smooth.bodyAngleX);

            // 3. Saccades & Restlessness micro-motion (low-amplitude noise function)
            const arousal = Math.max(cortisol, adrenaline);
            const microFreq = 1.0 + (arousal * 3.5); // 1Hz to 4.5Hz
            const microAmp = (0.05 + (arousal * 0.15)) * (1.0 - melatonin * 0.6);

            // Pseudo-random noise function (multi-frequency wave generator)
            const noise = (t: number) => Math.sin(t) * 0.65 + Math.cos(t * 1.83) * 0.25 + Math.sin(t * 3.42) * 0.10;

            const microTilt = noise(state.time * microFreq) * 2.0 * microAmp;
            const gazeMicroX = noise(state.time * microFreq * 0.85 + 1.0) * 0.22 * microAmp;
            const gazeMicroY = noise(state.time * microFreq * 0.95 + 2.0) * 0.15 * microAmp;

            smooth.eyeBallX = lerp(smooth.eyeBallX, targetEyeX + gazeMicroX, 5.0);
            smooth.eyeBallY = lerp(smooth.eyeBallY, targetEyeY + gazeMicroY, 5.0);
            core.setParameterValueById('ParamEyeBallX', smooth.eyeBallX);
            core.setParameterValueById('ParamEyeBallY', smooth.eyeBallY);

            // 4. Somatic Breathing & Physical Leaning (Respond to Adrenaline)
            const breathFreq = 1.5 + (adrenaline * 2.0) + (cortisol * 1.0);
            const somaticBreath = (Math.sin(state.time * breathFreq) * 0.5 + 0.5) * 0.02;
            core.setParameterValueById('ParamBodyAngleY', somaticBreath * 2);
            
            // Forward Leaning (Paramqq) triggers when dopamine is high
            const targetForwardLean = Math.max(0, (dopamine - 0.4) * 1.2) * leanIntensity;
            smooth.bodyAngleY = lerp(smooth.bodyAngleY, targetForwardLean, 3.0);
            core.setParameterValueById('Paramqq', smooth.bodyAngleY);

            // 5. High-Frequency Panic/Nervous Jitter (Cortisol & Adrenaline)
            if (cortisol > 0.6 || adrenaline > 0.7) {
                jitterPhase += delta * 25;
                const jitter = Math.sin(jitterPhase) * 0.15 * Math.max(cortisol, adrenaline) * jitterIntensity;
                core.setParameterValueById('Param141', 0.5 + jitter); // 慌张1
                core.setParameterValueById('Param142', 0.5 + Math.cos(jitterPhase * 0.8) * 0.1 * jitterIntensity); // 慌张2
                core.setParameterValueById('Param132', Math.min(1.0, Math.max(cortisol, adrenaline) * jitterIntensity)); // 慌張 state
            } else {
                core.setParameterValueById('Param141', 0);
                core.setParameterValueById('Param142', 0);
                core.setParameterValueById('Param132', 0);
            }

            // 6. Crying physics (High Cortisol + Low Dopamine)
            if (cortisol > 0.5 && dopamine < 0.45) {
                tearPhase += delta * (0.8 + cortisol * 1.2) * tearIntensity;
                const tearPulse = (Math.sin(tearPhase) * 0.5 + 0.5) * cortisol * tearIntensity;
                core.setParameterValueById('Param144', Math.min(1.0, cortisol * tearIntensity)); // 哭 state
                core.setParameterValueById('Param145', Math.min(1.0, tearPulse)); // 哭1
                core.setParameterValueById('Param146', Math.min(1.0, (Math.cos(tearPhase * 1.3) * 0.5 + 0.5) * cortisol * tearIntensity)); // 哭2
            } else {
                core.setParameterValueById('Param144', 0);
                core.setParameterValueById('Param145', 0);
                core.setParameterValueById('Param146', 0);
            }

            // 7. Boba wobble (Dynamic breast wobble/giggle reacting to speech and excitement)
            // Base wobble frequency and amplitude scale organically with adrenaline (excitement)
            let wFreq = 2.0 + (adrenaline * 3.0); 
            let wAmp = 2.0 * bobaIntensity * (1.0 + adrenaline * 1.5);
            
            let currentParam117 = 0;
            let currentParam119 = 0;

            if (curEmotion === 'boba') {
                // Maximum manual playfulness override (she is intentionally giggling/bouncing)
                currentParam117 += Math.sin(time * 10) * 15 * bobaIntensity;
                currentParam119 += Math.cos(time * 8) * 10 * bobaIntensity;
            }

            if (currentIsTalking && currentAmplitude > 5) {
                // High-frequency giggle vibrations (18Hz) triggered by voice amplitude
                const speechVibe = Math.sin(time * 18) * (currentAmplitude / 25) * bobaIntensity;
                const speechVibeY = Math.cos(time * 15) * (currentAmplitude / 30) * bobaIntensity;
                currentParam117 += Math.sin(time * wFreq) * wAmp + speechVibe * 3.0;
                currentParam119 += Math.cos(time * (wFreq * 0.8)) * wAmp + speechVibeY * 2.0;
            } else if (curEmotion !== 'boba') {
                // Gentle idle breathing sway (only if not explicitly bouncing)
                currentParam117 += Math.sin(time * wFreq) * wAmp;
                currentParam119 += Math.cos(time * (wFreq * 0.95)) * (wAmp * 0.75);
            }

            const base117 = core.getParameterValueById ? (core.getParameterValueById('Param117') || 0) : 0;
            const base119 = core.getParameterValueById ? (core.getParameterValueById('Param119') || 0) : 0;
            core.setParameterValueById('Param117', base117 + currentParam117);
            core.setParameterValueById('Param119', base119 + currentParam119);

            // 8. Cheek-Puffs & Annoyance (Cortisol + low Serotonin)
            let targetPout = 0.0;
            if (curEmotion === 'pout' || (cortisol > 0.4 && serotonin < 0.4)) {
                targetPout = Math.min(1.0, cortisol * 1.2) * poutIntensity;
            }
            smooth.pout = lerp(smooth.pout, targetPout, 3.0);
            core.setParameterValueById('Param15', smooth.pout); // 撅嘴
            core.setParameterValueById('Param16', smooth.pout * 0.7); // 鼓脸

            // 9. Natural Cheek Blushing (Shy / Romantic / Excited)
            let targetBlush = 0.0;
            if (curEmotion === 'shy' || curEmotion === 'romantic' || dopamine > 0.8) {
                targetBlush = Math.min(1.0, (0.4 + dopamine * 0.4 + adrenaline * 0.2) * blushIntensity);
            }
            smooth.blush = lerp(smooth.blush, targetBlush, 2.0); // slower blush response is more realistic
            core.setParameterValueById('ParamCheek', smooth.blush + Math.sin(time * 1.5) * 0.1 * blushIntensity);
            core.setParameterValueById('Param149', smooth.blush); // 害羞 overlay

            // 10. Tongue sticking out
            if (curEmotion === 'tongue') {
                core.setParameterValueById('Param22', 1.0); // 吐舌
            } else {
                core.setParameterValueById('Param22', 0);
            }

            if (currentIsTalking && currentAmplitude > 5) {
                const mouthOpen = Math.min((currentAmplitude / 65), 1.0); 
                core.setParameterValueById('ParamMouthOpenY', mouthOpen);
                
                // Form mouth shape: smile slightly while talking if happy/dopamine is high
                const mouthForm = (dopamine - 0.5) * 2.0 + Math.sin(time * 12) * 0.15;
                core.setParameterValueById('ParamMouthForm', Math.max(-1.0, Math.min(1.0, mouthForm))); 
            } else {
                // Keep default chemical smiling mouth when silent
                if (dopamine > 0.6) {
                    core.setParameterValueById('ParamMouthForm', (dopamine - 0.5) * 1.5);
                } else if (cortisol > 0.5) {
                    core.setParameterValueById('ParamMouthForm', -0.5); // Frown slightly
                } else {
                    core.setParameterValueById('ParamMouthForm', 0);
                }
                
                // Close mouth when not talking
                core.setParameterValueById('ParamMouthOpenY', 0);
            }

            // 12. Blinking & Gaze Expressions
            // Dopamine: Smiling Eyes
            const eyeSmile = Math.min(1.0, dopamine * 0.85);
            core.setParameterValueById('ParamEyeLSmile', eyeSmile);
            core.setParameterValueById('ParamEyeRSmile', eyeSmile);

            // Serotonin: Relaxed, warm half-lidded eyes
            const relaxedGaze = 1.0 - (serotonin * 0.25);
            let targetEyeOpen = relaxedGaze;

            // Adrenaline: Wide, alert eyes
            if (adrenaline > 0.65) {
                targetEyeOpen = Math.min(1.4, 1.0 + (adrenaline - 0.65) * 0.6);
            }

            // Sleepiness (Melatonin)
            if (melatonin > 0.3) {
                const sleepyMaxOpen = Math.max(0.3, 1.0 - (melatonin * 0.5 * melatoninIntensity));
                targetEyeOpen = Math.min(sleepyMaxOpen, targetEyeOpen);
            }

            // Run blinking animation
            state.blinkTimer += delta;
            if (melatonin > 0.3 && Math.random() < 0.002 * melatonin * melatoninIntensity) {
                // Trigger a heavy blink early
                state.blinkTimer = state.nextBlink - 0.05;
            }

            if (state.blinkTimer >= state.nextBlink) {
                const blinkDuration = 0.15;
                const blinkProgress = (state.blinkTimer - state.nextBlink) / blinkDuration;
                if (blinkProgress < 1) {
                    const blinkCurve = Math.sin(blinkProgress * Math.PI);
                    const eyeClose = targetEyeOpen * (1 - (blinkCurve * 0.95));
                    core.setParameterValueById('ParamEyeLOpen', eyeClose);
                    core.setParameterValueById('ParamEyeROpen', eyeClose);
                } else {
                    state.blinkTimer = 0;
                    state.nextBlink = 2 + Math.random() * 4;
                }
            } else {
                core.setParameterValueById('ParamEyeLOpen', targetEyeOpen);
                core.setParameterValueById('ParamEyeROpen', targetEyeOpen);
            }

            // Cortisol: Brow furrowing (Stress & worry)
            const browY = -1.0 * cortisol;
            const browAngle = -0.5 * cortisol;
            core.setParameterValueById('ParamBrowLY', browY);
            core.setParameterValueById('ParamBrowRY', browY);
            core.setParameterValueById('ParamBrowLAngle', browAngle);
            core.setParameterValueById('ParamBrowRAngle', browAngle);

            // 13. Oxytocin (Loving bonding head-tilt & soft blush overlay)
            let targetAngleZ = 0.0;
            if (oxytocin > 0.4) {
                targetAngleZ = Math.sin(time * 1.2) * 4.0 * oxytocin * oxytocinIntensity;
            }
            smooth.angleZ = lerp(smooth.angleZ, targetAngleZ, 4.0);
            core.setParameterValueById('ParamAngleZ', smooth.angleZ + microTilt);

            if (oxytocin > 0.4) {
                const extraBlush = Math.min(0.6, (oxytocin - 0.4) * 0.8 * oxytocinIntensity);
                core.setParameterValueById('ParamCheek', Math.min(1.0, core.getParameterValueById('ParamCheek') + extraBlush));
                core.setParameterValueById('Param149', Math.min(1.0, core.getParameterValueById('Param149') + extraBlush));
                
                const oxyEyeSmile = Math.min(1.0, oxytocin * 0.5 * oxytocinIntensity);
                core.setParameterValueById('ParamEyeLSmile', Math.min(1.0, core.getParameterValueById('ParamEyeLSmile') + oxyEyeSmile));
                core.setParameterValueById('ParamEyeRSmile', Math.min(1.0, core.getParameterValueById('ParamEyeRSmile') + oxyEyeSmile));
            }

          } catch (e) {
            // Handle parameters not available in older cubism models
          }
        });

        // Start idle motion
        try { model.motion('idle'); } catch (_) {}

        setLoaded(true);
        console.log('[Live2D] ✅ Model loaded successfully:', modelUrl);

      } catch (err: any) {
        console.error('[Live2D] ❌ Failed to initialize:', err);
        setError(err.message || 'Unknown error');
      }
    };

    init();

    return () => {
      destroyed = true;
      if (handleMouseMove) window.removeEventListener('mousemove', handleMouseMove);
      if (handleMouseLeave) document.removeEventListener('mouseleave', handleMouseLeave);
      if (mouseTimeout) clearTimeout(mouseTimeout);
      try {
        appRef.current?.destroy(false, { children: true, texture: true, baseTexture: true });
      } catch (_) {}
      appRef.current = null;
      modelRef.current = null;
    };
  }, [modelUrl]);

  // Handle Dynamic Scaling and Resizing without re-loading
  useEffect(() => {
    const model = modelRef.current;
    if (!model || !loaded || !appRef.current) return;

    // Resize PIXI renderer dynamically
    try {
      appRef.current.renderer.resize(width, height);
    } catch (_) {}

    const modelW = model.internalModel.originalWidth;
    const modelH = model.internalModel.originalHeight;
    
    const scaleBaseX = (width * 0.95) / modelW;
    const scaleBaseY = (height * 0.95) / modelH;
    const finalScale = Math.min(scaleBaseX, scaleBaseY) * externalScale;

    model.scale.set(finalScale);
    
    // Adjust vertical position based on scale and custom alignment offsets
    const vOffset = height * (0.1 + (externalScale - 1) * 0.15);
    model.position.set(width / 2 + offsetX, height / 2 + vOffset + offsetY);
  }, [externalScale, loaded, width, height, offsetX, offsetY]);

  // Map emotions → Vivian's actual .exp3.json filenames
  const EMOTION_MAP: Record<string, string> = {
    happy:      'idle',
    excited:    'idle',
    playful:    'idle',
    shy:        '害羞',
    embarrassed:'害羞',
    sad:        '哭',
    lonely:     '哭',
    angry:      '黑脸',
    frustrated: '黑脸',
    annoyed:    '白眼',
    sarcastic:  '白眼',
    anxious:    '慌张',
    worried:    '慌张',
    scared:     '慌张',
    surprised:  '慌张',
    calm:       'idle',
    neutral:    'idle',
    affectionate:'idle',
    romantic:   '害羞',
    pout:       'idle', // Handled via params
    tongue:     'idle', // Handled via params
    boba:       'idle', // Handled via params
  };

  // React to thinking state and emotion → swap expressions
  useEffect(() => {
    if (!modelRef.current) return;
    try {
      if (isThinking) {
        modelRef.current.motion('Scene1');
      } else {
        const exprName = EMOTION_MAP[emotion] || 'idle';
        if (exprName === 'idle') {
          // Clear previous expression and run idle motion
          const expMgr = modelRef.current.internalModel?.motionManager?.expressionManager;
          if (expMgr) expMgr.restoreExpression();
          modelRef.current.motion('idle');
        } else {
          modelRef.current.expression(exprName);
        }
      }
    } catch (_) {}
  }, [isThinking, emotion]);



  if (error) {
    return (
      <div
        style={{ width, height }}
        className="flex flex-col items-center justify-center text-center p-4 gap-2"
      >
        <div className="text-2xl">⚠️</div>
        <p className="text-[10px] text-red-400 font-mono leading-relaxed break-all">
          {error}
        </p>
      </div>
    );
  }

  return (
    <div
      style={{ width, height }}
      className="relative flex items-center justify-center pointer-events-none"
    >
      {!loaded && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="flex gap-1">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-1.5 h-1.5 rounded-full bg-[var(--acc)] animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        </div>
      )}
      <canvas
        ref={canvasRef}
        className="pointer-events-none"
        style={{ width: '100%', height: '100%', opacity: loaded ? 1 : 0, transition: 'opacity 0.5s ease' }}
      />
    </div>
  );
};
