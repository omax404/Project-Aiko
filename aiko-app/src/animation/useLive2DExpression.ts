/**
 * aiko-app/src/animation/useLive2DExpression.ts
 * AAA Live2D Character Animation System & Layered Blend Tree Engine.
 * 
 * Computes 6 real-time layers frame-by-frame:
 * Layer 1: Idle & Breathing (continuous breathing, sways, double-blinks, 1/f noise)
 * Layer 2: Eye & Head Gaze Tracking (critically-damped 2nd-order spring physics, anatomical clamping)
 * Layer 3: Secondary Motion & Physics (hair/clothing springs, emotional stiffness scaling)
 * Layer 4: Expression / Emotion Layer (350-500ms cubic-bezier cross-fade blender)
 * Layer 5: Lip-Sync Layer (real-time audio amplitude attack/release envelope)
 * Layer 6: Gesture & Reaction Layer (one-shot actions layering on top)
 */

import { useEffect, useRef, useCallback } from 'react';
import { mapEmotionToTargets, NeuromodulatorState } from './emotionMapper';
import { IdleLayer } from './idleLayer';
import { ExpressionBlender } from './expressionBlender';
import { GestureController } from './gestureController';
import { MultiSpringController } from './springSmoother';
import { ParamBinder } from './paramBinder';

export interface useLive2DExpressionOptions {
  loaded?: boolean;
  isThinking?: boolean;
  isTalking?: boolean;
  mouthAmplitude?: number; // 0.0 to 1.0 speech amplitude
  spokenText?: string;     // Currently spoken text for vowel lip sync
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

function emotionPreset(emotion: string): string | null {
  const normalized = emotion.trim().toLowerCase().replace(/[ _-]+/g, ' ');
  if (!normalized || normalized === 'neutral' || normalized === 'calm') return null;
  if (/happy|joy|excited|playful|curious|interested|amused/.test(normalized)) return 'happy';
  if (/shy|embarrass|romantic|affection|flirt/.test(normalized)) return 'shy';
  if (/sad|lonely|disappoint|grief/.test(normalized)) return 'sad';
  if (/angry|frustrat|annoy|sarcastic|pout/.test(normalized)) return 'pouty';
  if (/anxious|worried|scared|afraid|surpris|shock/.test(normalized)) return 'surprised';
  if (/sleep|tired|bored/.test(normalized)) return 'sleepy';
  return null;
}

export function useLive2DExpression(
  modelRef: React.RefObject<any>,
  emotionState: NeuromodulatorState | null,
  options: useLive2DExpressionOptions = {}
) {
  const { loaded = false, isThinking = false, isTalking = false, mouthAmplitude = 0 } = options;
  const emotion = options.emotion || 'neutral';

  const binderRef = useRef<ParamBinder | null>(null);
  const idleLayerRef = useRef(new IdleLayer());
  const expressionBlenderRef = useRef(new ExpressionBlender());
  const gestureControllerRef = useRef(new GestureController());
  const springControllerRef = useRef(new MultiSpringController());

  // Mouse / Eye Gaze Spring State (Layer 2)
  const targetGazeRef = useRef({ x: 0, y: 0 });
  const currentGazeRef = useRef({ x: 0, y: 0 });

  // Lip-Sync Envelope State (Layer 5)
  const smoothedAmplitudeRef = useRef(0);
  const isTalkingRef = useRef(isTalking);
  const rawMouthAmplitudeRef = useRef(mouthAmplitude);
  const emotionStateRef = useRef<NeuromodulatorState | null>(emotionState);

  useEffect(() => { isTalkingRef.current = isTalking; }, [isTalking]);
  useEffect(() => { rawMouthAmplitudeRef.current = mouthAmplitude; }, [mouthAmplitude]);
  useEffect(() => { emotionStateRef.current = emotionState; }, [emotionState]);

  // Interactive Mouse Cursor Tracking with Critically-Damped Easing
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const winWidth = window.innerWidth || 1920;
      const winHeight = window.innerHeight || 1080;
      // Map cursor position to normalized [-0.8, 0.8] gaze range
      const normX = ((e.clientX / winWidth) - 0.5) * 1.6;
      const normY = ((e.clientY / winHeight) - 0.5) * 1.2;
      targetGazeRef.current = {
        x: Math.max(-0.8, Math.min(0.8, normX)),
        y: Math.max(-0.6, Math.min(0.6, normY)),
      };
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // Use Aiko's semantic mood first; let chemistry gently shape a neutral state.
  useEffect(() => {
    const chemistry = emotionState || DEFAULT_CHEMISTRY;
    const explicitMood = emotionPreset(emotion);
    const dopamine = chemistry.dopamine ?? 0.5;
    const serotonin = chemistry.serotonin ?? 0.5;
    const cortisol = chemistry.cortisol ?? 0.2;
    const adrenaline = chemistry.adrenaline ?? 0.1;
    const oxytocin = chemistry.oxytocin ?? 0.3;
    const preset = isThinking
      ? 'sleepy'
      : explicitMood || (
        oxytocin > 0.75 ? 'shy'
          : adrenaline > 0.72 ? 'surprised'
            : dopamine > 0.76 ? 'happy'
              : cortisol > 0.78 ? 'pouty'
                : serotonin < 0.2 ? 'sad'
                  : 'neutral'
      );
    const intensity = preset === 'neutral' ? 0.58 : preset === 'sleepy' ? 0.52 : 0.78;
    expressionBlenderRef.current.setExpression(preset, intensity, 650);
  }, [emotionState, emotion, isThinking]);

  // CLEAN PUBLIC API EXPOSED TO CHAT / AI LOGIC LAYER
  const triggerExpression = useCallback((name: string, intensity: number = 1.0, durationMs: number = 400) => {
    console.log(`[AnimationEngine] Triggering Expression: ${name} (intensity: ${intensity})`);
    expressionBlenderRef.current.setExpression(name, intensity, durationMs);
  }, []);

  const playGesture = useCallback((gestureName: string) => {
    console.log(`[AnimationEngine] Playing Gesture: ${gestureName}`);
    return gestureControllerRef.current.playGesture(gestureName);
  }, []);

  const setGaze = useCallback((x: number, y: number) => {
    targetGazeRef.current = {
      x: Math.max(-0.8, Math.min(0.8, x)),
      y: Math.max(-0.6, Math.min(0.6, y))
    };
  }, []);

  // Main 60 FPS Layered Animation Render Loop
  useEffect(() => {
    if (!loaded || !modelRef.current) return;

    const model = modelRef.current;
    if (!binderRef.current) {
      binderRef.current = new ParamBinder(model);
    }

    let animFrameId: number;
    let lastTime = performance.now();

    const loop = (now: number) => {
      const dt = Math.min(0.05, (now - lastTime) / 1000.0); // Clamp dt to prevent frame lag spikes
      lastTime = now;

      // 1. Layer 1: Procedural Idle & Breathing Calculations
      const chemistry = emotionStateRef.current || DEFAULT_CHEMISTRY;
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

      // 4. Layer 5: Lip-Sync Attack/Release Envelope
      const rawAmp = rawMouthAmplitudeRef.current;
      const attackRate = 25.0;  // Fast attack on speech start
      const releaseRate = 12.0; // Smooth release envelope to prevent jittery mouth flapping
      
      if (rawAmp > smoothedAmplitudeRef.current) {
        smoothedAmplitudeRef.current += (rawAmp - smoothedAmplitudeRef.current) * Math.min(1.0, dt * attackRate);
      } else {
        smoothedAmplitudeRef.current += (rawAmp - smoothedAmplitudeRef.current) * Math.min(1.0, dt * releaseRate);
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
          isTalkingRef.current,
          smoothedAmplitudeRef.current
        );
      }

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
