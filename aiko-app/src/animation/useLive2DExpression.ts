/**
 * aiko-app/src/animation/useLive2DExpression.ts
 * AAA Live2D Character Animation System & Layered Blend Tree Engine.
 *
 * Synchronized directly with Live2D's `internalModel.on('beforeModelUpdate')` hook
 * so all 6 procedural layers apply immediately before Cubism Physics (`vivian.physics3.json`)
 * and mesh vertex updates (`coreModel.update()`).
 *
 * Computes 6 real-time layers frame-by-frame:
 * Layer 1: Idle & Breathing (multi-harmonic breathing, sways, asymmetric blinks, conversational cadence)
 * Layer 2: Eye & Head Gaze Tracking (critically-damped 2nd-order spring physics, anatomical clamping)
 * Layer 3: Secondary Motion & Physics (shoulder/hip counter-sway + Live2D hair/cloth physics integration)
 * Layer 4: Expression / Emotion Layer (cubic-bezier cross-fade blender)
 * Layer 5: Lip-Sync + Vowel Formant Layer (audio amplitude envelope + text syllable/vowel synthesis)
 * Layer 6: Gesture & Reaction Layer (one-shot actions layering on top)
 */

import { useEffect, useRef, useCallback } from 'react';
import { mapEmotionToTargets, NeuromodulatorState } from './emotionMapper';
import { resolveEmotionProfile } from './emotionProfile';
import { IdleLayer } from './idleLayer';
import { ExpressionBlender } from './expressionBlender';
import { GestureController } from './gestureController';
import { MultiSpringController } from './springSmoother';
import { ParamBinder } from './paramBinder';
import { useNeuralStore } from '../store/useNeuralStore';

export interface useLive2DExpressionOptions {
  loaded?: boolean;
  isThinking?: boolean;
  isTalking?: boolean;
  mouthAmplitude?: number; // 0.0 to 1.0 speech amplitude
  spokenText?: string;     // Optional override text for vowel lip sync
  emotion?: string;
}

const DEFAULT_CHEMISTRY: NeuromodulatorState = {
  dopamine: 0.5,
  serotonin: 0.5,
  cortisol: 0.2,
  adrenaline: 0.1,
  oxytocin: 0.3,
  melatonin: 0.1,
};

/**
 * Estimates a subtle vowel mouth-form target (-0.35 for rounded 'o'/'u' to +0.35 for wide 'a'/'e'/'i')
 * and synthetic syllable amplitude when text is actively streaming or spoken.
 */
function computeSpeechArticulation(
  text: string,
  nowSec: number
): { syntheticAmp: number; vowelForm: number } {
  if (!text) return { syntheticAmp: 0, vowelForm: 0 };
  const clean = text.replace(/[*_~`#[\]()<>]/g, '').trim();
  if (!clean) return { syntheticAmp: 0, vowelForm: 0 };

  // Scan along the tail of the spoken text at ~13 chars/sec
  const idx = Math.min(clean.length - 1, Math.floor((nowSec * 13) % Math.max(1, Math.min(clean.length, 48))));
  const ch = (clean[clean.length - 1 - idx] || '').toLowerCase();

  let vowelForm = 0;
  let charEnergy = 0.32;
  if (ch === 'a' || ch === 'e' || ch === 'i') {
    vowelForm = 0.28;
    charEnergy = 0.52;
  } else if (ch === 'o' || ch === 'u' || ch === 'w') {
    vowelForm = -0.28;
    charEnergy = 0.46;
  } else if (' .,!?;:—-\n'.includes(ch)) {
    charEnergy = 0.04;
  }

  // Multi-sine syllable envelope (~5.5 Hz jaw cadence)
  const syllableWave = Math.max(
    0,
    Math.sin(nowSec * 34.0) * 0.55 + Math.sin(nowSec * 19.0 + 0.8) * 0.45
  );
  return {
    syntheticAmp: charEnergy * syllableWave,
    vowelForm,
  };
}

export function useLive2DExpression(
  modelRef: React.RefObject<any>,
  emotionState: NeuromodulatorState | null,
  options: useLive2DExpressionOptions = {}
) {
  const { loaded = false, isThinking = false, isTalking = false, mouthAmplitude = 0, spokenText = '' } = options;
  const emotion = options.emotion || 'neutral';

  const binderRef = useRef<ParamBinder | null>(null);
  const idleLayerRef = useRef(new IdleLayer());
  const expressionBlenderRef = useRef(new ExpressionBlender());
  const gestureControllerRef = useRef(new GestureController());
  const springControllerRef = useRef(new MultiSpringController());

  // Mouse / Eye Gaze Spring State (Layer 2)
  const targetGazeRef = useRef({ x: 0, y: 0 });
  const currentGazeRef = useRef({ x: 0, y: 0 });
  const lastMouseMoveTimeRef = useRef<number>(0);

  // Lip-Sync Envelope State (Layer 5)
  const smoothedAmplitudeRef = useRef(0);
  const isTalkingPropRef = useRef(isTalking);
  const rawMouthAmplitudePropRef = useRef(mouthAmplitude);
  const spokenTextPropRef = useRef(spokenText);
  const emotionStatePropRef = useRef<NeuromodulatorState | null>(emotionState);

  useEffect(() => { isTalkingPropRef.current = isTalking; }, [isTalking]);
  useEffect(() => { rawMouthAmplitudePropRef.current = mouthAmplitude; }, [mouthAmplitude]);
  useEffect(() => { spokenTextPropRef.current = spokenText; }, [spokenText]);
  useEffect(() => { emotionStatePropRef.current = emotionState; }, [emotionState]);

  // Register smooth gaze springs
  useEffect(() => {
    springControllerRef.current.register('gazeX', 0, 9);
    springControllerRef.current.register('gazeY', 0, 9);
  }, []);

  // Interactive Mouse Cursor Tracking with Smooth Idle Return
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const winWidth = window.innerWidth || 1920;
      const winHeight = window.innerHeight || 1080;
      const normX = ((e.clientX / winWidth) - 0.5) * 1.5;
      const normY = -((e.clientY / winHeight) - 0.5) * 1.1; // Invert Y so up cursor = look up
      targetGazeRef.current = {
        x: Math.max(-0.8, Math.min(0.8, normX)),
        y: Math.max(-0.6, Math.min(0.6, normY)),
      };
      lastMouseMoveTimeRef.current = performance.now();
    };
    const handleMouseLeave = () => {
      targetGazeRef.current = { x: 0, y: 0 };
    };
    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('mouseleave', handleMouseLeave, { passive: true });
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  // Use Aiko's semantic mood first; let chemistry gently shape a neutral state.
  useEffect(() => {
    const chemistry = emotionState || DEFAULT_CHEMISTRY;
    const explicitMood = resolveEmotionProfile(emotion).expression;
    const dopamine = chemistry.dopamine ?? 0.5;
    const serotonin = chemistry.serotonin ?? 0.5;
    const cortisol = chemistry.cortisol ?? 0.2;
    const adrenaline = chemistry.adrenaline ?? 0.1;
    const oxytocin = chemistry.oxytocin ?? 0.3;
    const preset = isThinking
      ? 'neutral'
      : explicitMood !== 'neutral' ? explicitMood : (
        oxytocin > 0.75 ? 'shy'
          : adrenaline > 0.72 ? 'surprised'
            : dopamine > 0.76 ? 'happy'
              : cortisol > 0.78 ? 'pouty'
                : serotonin < 0.2 ? 'sad'
                  : 'neutral'
      );
    const intensity = preset === 'neutral' ? 0.58 : preset === 'sleepy' ? 0.52 : 0.78;
    expressionBlenderRef.current.setExpression(preset, intensity, 520);
  }, [emotionState, emotion, isThinking]);

  const triggerExpression = useCallback((name: string, intensity: number = 1.0, durationMs: number = 420) => {
    expressionBlenderRef.current.setExpression(name, intensity, durationMs);
  }, []);

  const playGesture = useCallback((gestureName: string) => {
    return gestureControllerRef.current.playGesture(gestureName);
  }, []);

  const setGaze = useCallback((x: number, y: number) => {
    targetGazeRef.current = {
      x: Math.max(-0.8, Math.min(0.8, x)),
      y: Math.max(-0.6, Math.min(0.6, y))
    };
    lastMouseMoveTimeRef.current = performance.now();
  }, []);

  // Main Layered Animation Render Loop (hooked into Live2D `beforeModelUpdate` when available)
  useEffect(() => {
    if (!loaded || !modelRef.current) return;

    const model = modelRef.current;
    binderRef.current = new ParamBinder(model);

    let lastTime = performance.now();

    const stepFrame = (now: number) => {
      const dt = Math.max(0.001, Math.min(0.05, (now - lastTime) / 1000.0));
      lastTime = now;

      // Read high-frequency transient state directly from store without React re-renders
      const storeState = useNeuralStore.getState();
      const chemistry = emotionStatePropRef.current || storeState.chemicals || DEFAULT_CHEMISTRY;
      const liveTalking = Boolean(isTalkingPropRef.current || storeState.isTalking || storeState.streamingContent);
      const liveRawAmp = Math.max(rawMouthAmplitudePropRef.current || 0, storeState.amplitude || 0);
      const activeText =
        spokenTextPropRef.current ||
        storeState.streamingContent ||
        (liveTalking ? storeState.messages[storeState.messages.length - 1]?.content || '' : '');

      // Smoothly return gaze toward center after 4s of mouse inactivity
      if (lastMouseMoveTimeRef.current > 0 && now - lastMouseMoveTimeRef.current > 4000) {
        targetGazeRef.current = {
          x: targetGazeRef.current.x * Math.exp(-1.5 * dt),
          y: targetGazeRef.current.y * Math.exp(-1.5 * dt),
        };
      }

      // 1. Layer 1: Procedural Idle & Breathing Calculations
      const mappedEmotion = mapEmotionToTargets(chemistry);
      const idleOutputs = idleLayerRef.current.update(
        dt,
        mappedEmotion.blinkRate,
        mappedEmotion.breathDepth,
        chemistry.cortisol ?? 0.2,
        chemistry.adrenaline ?? 0.1,
        chemistry.dopamine ?? 0.5,
        smoothedAmplitudeRef.current
      );

      // 2. Layer 2: Eye & Head Tracking Physics (Critically Damped Spring)
      const targetGaze = targetGazeRef.current;
      const gazeX = springControllerRef.current.update('gazeX', targetGaze.x, dt);
      const gazeY = springControllerRef.current.update('gazeY', targetGaze.y, dt);
      currentGazeRef.current = { x: gazeX, y: gazeY };

      // 3. Layer 4: Expression Cross-Fade Blender
      const blendedExpression = expressionBlenderRef.current.update(dt);

      // 4. Layer 5: Lip-Sync Attack/Release Envelope + Vowel Formant Synthesis
      const { syntheticAmp, vowelForm } = liveTalking
        ? computeSpeechArticulation(activeText, now / 1000.0)
        : { syntheticAmp: 0, vowelForm: 0 };
      const effectiveTargetAmp = liveRawAmp > 0.02 ? liveRawAmp : syntheticAmp;

      const attackRate = 28.0;  // Fast attack on phoneme onset
      const releaseRate = 14.0; // Smooth release envelope
      if (effectiveTargetAmp > smoothedAmplitudeRef.current) {
        smoothedAmplitudeRef.current += (effectiveTargetAmp - smoothedAmplitudeRef.current) * Math.min(1.0, dt * attackRate);
      } else {
        smoothedAmplitudeRef.current += (effectiveTargetAmp - smoothedAmplitudeRef.current) * Math.min(1.0, dt * releaseRate);
      }

      // 5. Layer 6: One-Shot Gesture Reaction Layer
      const gestureOffsets = gestureControllerRef.current.update(dt);

      // 6. Bind all 6 layers onto Live2D core parameters
      const coreModel = model.internalModel?.coreModel || model;
      if (coreModel && binderRef.current) {
        binderRef.current.bind(
          coreModel,
          blendedExpression,
          idleOutputs,
          currentGazeRef.current,
          gestureOffsets,
          liveTalking,
          smoothedAmplitudeRef.current,
          dt,
          vowelForm
        );
      }
    };

    const internalModel = model.internalModel;
    if (internalModel && typeof internalModel.on === 'function') {
      const onBeforeModelUpdate = () => {
        stepFrame(performance.now());
      };
      internalModel.on('beforeModelUpdate', onBeforeModelUpdate);
      return () => {
        if (typeof internalModel.off === 'function') {
          internalModel.off('beforeModelUpdate', onBeforeModelUpdate);
        } else if (typeof internalModel.removeListener === 'function') {
          internalModel.removeListener('beforeModelUpdate', onBeforeModelUpdate);
        }
      };
    }

    // Fallback for test mocks or standalone models without EventEmitter
    let animFrameId: number;
    const loop = (now: number) => {
      stepFrame(now);
      animFrameId = requestAnimationFrame(loop);
    };
    animFrameId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animFrameId);
  }, [loaded, modelRef]);

  return {
    triggerExpression,
    triggerDiscreteExpression: triggerExpression,
    playGesture,
    setGaze
  };
}
