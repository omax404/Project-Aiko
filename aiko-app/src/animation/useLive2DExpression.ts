import { useEffect, useRef, useState } from 'react';
import { NeuromodulatorState, ExpressionTargets, mapEmotionToTargets } from './emotionMapper';
import { IdleLayer } from './idleLayer';
import { MultiSpringController } from './springSmoother';
import { ParamBinder } from './paramBinder';

export interface TransientExpression {
  name: string;
  targets: Partial<ExpressionTargets>;
  duration: number; // in milliseconds
  elapsed: number;   // elapsed time in milliseconds
}

export interface useLive2DExpressionOptions {
  loaded?: boolean;
  isTalking?: boolean;
  mouthAmplitude?: number; // 0.0 to 1.0 speech amplitude
  spokenText?: string;     // Currently spoken text for vowel lip sync
  stiffnessOverrides?: Partial<Record<keyof ExpressionTargets, number>>;
}

/**
 * React hook that drives a physics-based, procedurally animated emotional expression
 * pipeline for a pixi-live2d-display model.
 */
export function useLive2DExpression(
  modelRef: React.RefObject<any>,
  emotionState: NeuromodulatorState | null,
  options: useLive2DExpressionOptions = {}
) {
  const { loaded = false, isTalking = false, mouthAmplitude = 0, spokenText = '', stiffnessOverrides = {} } = options;

  // Debug state for overlay visualizer (updated less frequently to avoid rendering overhead)
  const [debugState, setDebugState] = useState<{
    targets: ExpressionTargets | null;
    currentSprings: Record<string, number>;
  }>({ targets: null, currentSprings: {} });

  const binderRef = useRef<ParamBinder | null>(null);
  const idleLayerRef = useRef(new IdleLayer());
  const springControllerRef = useRef(new MultiSpringController());
  
  // Track active transient overrides (discrete actions like wink/surprised)
  const transientOverridesRef = useRef<TransientExpression[]>([]);

  // Keep references to values to avoid closure lock in requestAnimationFrame
  const isTalkingRef = useRef(isTalking);
  const mouthAmplitudeRef = useRef(mouthAmplitude);
  useEffect(() => { isTalkingRef.current = isTalking; }, [isTalking]);
  useEffect(() => { mouthAmplitudeRef.current = mouthAmplitude; }, [mouthAmplitude]);

  // Vowel Lip-Sync Buffer State
  const vowelsRef = useRef<string[]>([]);
  const vowelIndexRef = useRef(0);
  const vowelTimerRef = useRef(0);
  const lastProcessedTextRef = useRef('');

  // Extract vowels dynamically from text stream
  useEffect(() => {
    if (!spokenText) {
      vowelsRef.current = [];
      vowelIndexRef.current = 0;
      vowelTimerRef.current = 0;
      lastProcessedTextRef.current = '';
      return;
    }

    if (spokenText.startsWith(lastProcessedTextRef.current)) {
      const newChars = spokenText.slice(lastProcessedTextRef.current.length);
      const filtered = newChars.toLowerCase().replace(/[^aeiou]/g, '').split('');
      if (filtered.length > 0) {
        vowelsRef.current = [...vowelsRef.current, ...filtered].slice(-100); // Buffer up to 100 vowels
      }
      lastProcessedTextRef.current = spokenText;
    } else {
      // Full reset or new utterance
      const filtered = spokenText.toLowerCase().replace(/[^aeiou]/g, '').split('');
      vowelsRef.current = filtered.slice(-100);
      vowelIndexRef.current = 0;
      vowelTimerRef.current = 0;
      lastProcessedTextRef.current = spokenText;
    }
  }, [spokenText]);

  // Track raw chemicals for idle animation modifiers (panic, crying)
  const chemicalsRef = useRef({ dopamine: 0.5, cortisol: 0.0, adrenaline: 0.0, valence: 0.0 });
  useEffect(() => {
    if (emotionState) {
      const valence = emotionState.valence ?? (0.4 * emotionState.serotonin + 0.4 * emotionState.dopamine - 0.5 * emotionState.cortisol - 0.3 * emotionState.adrenaline);
      chemicalsRef.current = {
        dopamine: emotionState.dopamine,
        cortisol: emotionState.cortisol,
        adrenaline: emotionState.adrenaline,
        valence
      };
    }
  }, [emotionState]);

  // Last known neuromodulator state mapped immediately
  const ambientTargetsRef = useRef<ExpressionTargets>({
    eyeOpenness: 1.0,
    browTension: 0.0,
    mouthCurve: 0.0,
    mouthOpen: 0.0,
    headTiltX: 0.0,
    headTiltY: 0.0,
    headTiltZ: 0.0,
    bodySway: 0.0,
    blinkRate: 4.0,
    breathDepth: 1.0,
    blush: 0.0
  });

  // Map incoming emotion state stream on change
  useEffect(() => {
    if (emotionState) {
      ambientTargetsRef.current = mapEmotionToTargets(emotionState);
    }
  }, [emotionState]);

  // Public method to trigger discrete temporary overrides (chat events etc.)
  const triggerDiscreteExpression = (name: string, targets: Partial<ExpressionTargets>, durationMs: number = 1000) => {
    // Evict any conflicting override with the same name
    transientOverridesRef.current = transientOverridesRef.current.filter(e => e.name !== name);
    transientOverridesRef.current.push({
      name,
      targets,
      duration: durationMs,
      elapsed: 0
    });
  };

  useEffect(() => {
    const model = modelRef.current;
    if (!model || !loaded) return;

    // Instantiate binder dynamically with parameter discovery
    if (!binderRef.current) {
      binderRef.current = new ParamBinder(model);
    } else {
      binderRef.current.refreshParameters(model);
    }

    const binder = binderRef.current;
    const idleLayer = idleLayerRef.current;
    const springController = springControllerRef.current;

    // Define initial spring parameters (low stiffness for head inertia, high for eyes/mouth)
    const baseStiffness: Record<keyof ExpressionTargets, number> = {
      eyeOpenness: 18.0,
      browTension: 12.0,
      mouthCurve: 10.0,
      mouthOpen: 18.0,
      headTiltX: 5.5,
      headTiltY: 5.5,
      headTiltZ: 6.0,
      bodySway: 4.0,
      blinkRate: 10.0,
      breathDepth: 10.0,
      blush: 8.0
    };

    // Register springs with default or overridden stiffness values
    Object.keys(baseStiffness).forEach(k => {
      const key = k as keyof ExpressionTargets;
      const stiffness = stiffnessOverrides[key] ?? baseStiffness[key];
      springController.register(key, ambientTargetsRef.current[key], stiffness);
    });

    let lastTime = performance.now();
    let animationFrameId: number;
    let debugTimer = 0;

    // requestAnimationFrame 60fps update loop decoupled from WebSocket stream rate
    const tick = (now: number) => {
      const dt = Math.min(0.05, (now - lastTime) / 1000.0); // clamp dt to prevent giant jumps when tab suspends
      lastTime = now;

      // 1. Process transient discrete overrides
      const transientTargets: Partial<ExpressionTargets> = {};
      const activeOverrides: TransientExpression[] = [];

      transientOverridesRef.current.forEach(ovr => {
        ovr.elapsed += dt * 1000;
        if (ovr.elapsed < ovr.duration) {
          activeOverrides.push(ovr);
          
          // Calculate ease-in/ease-out envelope weight (0.0 -> 1.0 -> 0.0)
          const lifeRatio = ovr.elapsed / ovr.duration;
          const weight = Math.sin(lifeRatio * Math.PI); // Half sine curve

          // Blend override targets
          Object.keys(ovr.targets).forEach(k => {
            const key = k as keyof ExpressionTargets;
            const targetVal = ovr.targets[key];
            if (targetVal !== undefined) {
              const currentAccum = transientTargets[key] ?? 0;
              transientTargets[key] = currentAccum + targetVal * weight;
            }
          });
        }
      });
      // Save still-active overrides
      transientOverridesRef.current = activeOverrides;

      // 2. Blend ambient targets with transient overrides
      const blendedTargets: ExpressionTargets = { ...ambientTargetsRef.current };
      Object.keys(transientTargets).forEach(k => {
        const key = k as keyof ExpressionTargets;
        const offset = transientTargets[key];
        if (offset !== undefined) {
          if (key === 'eyeOpenness') {
            blendedTargets.eyeOpenness = Math.max(0.0, blendedTargets.eyeOpenness + offset);
          } else {
            blendedTargets[key] = blendedTargets[key] + offset;
          }
        }
      });

      // 3. Run blended targets through the Spring Easing Controller
      const smoothedTargets: ExpressionTargets = { ...blendedTargets };
      Object.keys(blendedTargets).forEach(k => {
        const key = k as keyof ExpressionTargets;
        smoothedTargets[key] = springController.update(key, blendedTargets[key], dt);
      });

      // 4. Calculate Vowel-based Lip Sync
      let finalMouthOpen = smoothedTargets.mouthOpen;
      let finalMouthCurve = smoothedTargets.mouthCurve;

      if (isTalkingRef.current && mouthAmplitudeRef.current > 0.05) {
        let currentVowel = 'a';
        vowelTimerRef.current += dt;

        if (vowelsRef.current.length > 0) {
          // Transition syllable vowels smoothly
          if (vowelTimerRef.current >= 0.12) {
            vowelTimerRef.current = 0;
            vowelIndexRef.current = (vowelIndexRef.current + 1) % vowelsRef.current.length;
          }
          currentVowel = vowelsRef.current[vowelIndexRef.current] || 'a';
        } else {
          // Fallback to random natural babble vowels
          if (vowelTimerRef.current >= 0.15) {
            vowelTimerRef.current = 0;
            vowelIndexRef.current = Math.floor(Math.random() * 5);
          }
          currentVowel = ['a', 'e', 'i', 'o', 'u'][vowelIndexRef.current];
        }

        // Vowel parameters mappings (MouthOpenY, MouthForm)
        let targetOpenY = 0.55;
        let targetForm = 0.0;

        switch (currentVowel) {
          case 'a': // wide open
            targetOpenY = 0.95;
            targetForm = 0.2;
            break;
          case 'e': // mid open, smiling wide
            targetOpenY = 0.6;
            targetForm = 0.55;
            break;
          case 'i': // narrow open, smiling very wide
            targetOpenY = 0.35;
            targetForm = 0.85;
            break;
          case 'o': // wide open, round shape
            targetOpenY = 0.85;
            targetForm = -0.55;
            break;
          case 'u': // narrow open, rounded shape
            targetOpenY = 0.45;
            targetForm = -0.85;
            break;
        }

        // Modulate with speech amplitude envelope
        const envelope = Math.min(mouthAmplitudeRef.current * 1.5, 1.0);
        finalMouthOpen = targetOpenY * envelope;
        
        // Combine vowel shape form with base emotional curve + small micro-noise for jitters
        const noise = Math.sin(now * 0.025) * 0.06;
        finalMouthCurve = Math.max(-1.0, Math.min(1.0, targetForm + (chemicalsRef.current.valence * 0.5) + noise));
      }

      // Apply the final values to mouth targets
      smoothedTargets.mouthOpen = finalMouthOpen;
      smoothedTargets.mouthCurve = finalMouthCurve;

      // 5. Update procedural idle layers (blinking timing, look saccades, head sways, dynamic crying, panic, boba)
      const chem = chemicalsRef.current;
      const idleOutputs = idleLayer.update(
        dt,
        smoothedTargets.blinkRate,
        smoothedTargets.breathDepth,
        chem.cortisol,
        chem.adrenaline,
        chem.dopamine,
        mouthAmplitudeRef.current
      );

      // 6. Bind resulting values to actual model parameters via ParamBinder
      if (model.internalModel?.coreModel) {
        // Manually update the model state (motions, physics) first
        try {
          model.update(dt * 1000);
        } catch (_) {}

        binder.bind(
          model.internalModel.coreModel,
          smoothedTargets,
          idleOutputs,
          isTalkingRef.current,
          mouthAmplitudeRef.current,
          chem.cortisol,
          chem.adrenaline
        );
      }

      // 7. Update debug overlay state periodically (every 100ms) to conserve performance
      debugTimer += dt;
      if (debugTimer >= 0.1) {
        debugTimer = 0;
        const currentVals: Record<string, number> = {};
        Object.keys(smoothedTargets).forEach(k => {
          currentVals[k] = springController.getVal(k);
        });
        setDebugState({
          targets: { ...blendedTargets },
          currentSprings: currentVals
        });
      }

      animationFrameId = requestAnimationFrame(tick);
    };

    animationFrameId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [modelRef, loaded, stiffnessOverrides]);

  return {
    triggerDiscreteExpression,
    debugState
  };
}
