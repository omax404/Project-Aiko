import React, { useEffect, useRef, useState } from 'react';
import { useNeuralStore } from '../store/useNeuralStore';
import { useShallow } from 'zustand/react/shallow';
import { useLive2DExpression } from '../animation/useLive2DExpression';

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
  const {
    chemicals: storeChemicals,
    streamingContent,
    messages
  } = useNeuralStore(useShallow((state) => ({
    chemicals: state.chemicals,
    streamingContent: state.streamingContent,
    messages: state.messages
  })));
  const currentChemicals = chemicals || storeChemicals;

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const appRef = useRef<any>(null);
  const modelRef = useRef<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  // Hook driving autonomous expression physics, blink, saccade, breathing, boba, and vowel lip sync loops
  const { triggerDiscreteExpression } = useLive2DExpression(modelRef, currentChemicals, {
    loaded,
    isTalking,
    mouthAmplitude: amplitude,
    spokenText: isThinking ? '' : (streamingContent || (messages.length > 0 ? messages[messages.length - 1].content : ''))
  });

  const lastParsedTextRef = useRef('');

  useEffect(() => {
    const latestText = isThinking 
      ? '' 
      : (streamingContent || (messages.length > 0 ? messages[messages.length - 1].content : ''));
      
    if (!latestText || latestText === lastParsedTextRef.current) return;
    
    // Scan for new [gesture:xxx] or [mood:xxx] tags
    const tagRegex = /\[(gesture|mood):([a-zA-Z0-9_\-]+)\]/g;
    let match;
    const model = modelRef.current;
    if (!model) return;
    
    const newContent = latestText.slice(lastParsedTextRef.current.length);
    lastParsedTextRef.current = latestText;
    
    while ((match = tagRegex.exec(newContent)) !== null) {
      const type = match[1];
      const name = match[2];
      
      console.log(`[Live2D Autonomy] Parsed action tag: [${type}:${name}]`);
      try {
        if (type === 'gesture') {
          if (name === 'wave' || name === 'nod' || name === 'point' || name === 'bow') {
            model.motion('Scene1');
          } else {
            model.motion(name);
          }
        } else if (type === 'mood') {
          if (name === 'excited' || name === 'happy') {
            model.expression('害羞');
          } else if (name === 'sad' || name === 'crying') {
            model.expression('哭');
          } else {
            model.expression(name);
          }
        }
      } catch (err) {
        console.warn(`[Live2D Autonomy] Failed to play tag [${type}:${name}]:`, err);
      }
    }

    // === AIKO WILL: Semantic Gesture & Sentiment Mapping via transient springs ===
    const lowerText = newContent.toLowerCase();
    
    // Question triggers -> Curious head tilt
    if (lowerText.includes('?') || /\b(why|how|what|who|where|curious|wonder)\b/.test(lowerText)) {
      triggerDiscreteExpression('curious_tilt', { headTiltZ: -0.22, headTiltY: -0.1 }, 1600);
    }
    // Surprise / Excitement triggers -> Perk up
    else if (lowerText.includes('!') || /\b(wow|amazing|awesome|cool|oh|surprised|gasp)\b/.test(lowerText)) {
      triggerDiscreteExpression('perk_up', { headTiltY: 0.18, eyeOpenness: 0.15 }, 1100);
    }
    // Agreement triggers -> Nod agree
    else if (/\b(yes|yeah|agree|nod|indeed|exactly|correct|sure|alright)\b/.test(lowerText)) {
      triggerDiscreteExpression('nod', { headTiltY: -0.18 }, 900);
    }
    // Disagreement triggers -> Shake head
    else if (/\b(no|never|disagree|don't|not|impossible|stop|nope)\b/.test(lowerText)) {
      triggerDiscreteExpression('shake', { headTiltX: -0.25 }, 900);
    }
    // Affection triggers -> Shy look away
    else if (/\b(love|cute|blush|hug|heart|shy|embarrassed|hehe|hihi)\b/.test(lowerText)) {
      triggerDiscreteExpression('shy_look', { headTiltX: 0.18, headTiltZ: 0.12 }, 1800);
    }
  }, [streamingContent, messages, isThinking]);

  useEffect(() => {
    if (isThinking) {
      // Look up and away randomly to process information (cognitive lookup)
      triggerDiscreteExpression('thinking', { headTiltX: 0.35, headTiltY: 0.25, browTension: 0.2 }, 3000);
    }
  }, [isThinking]);

  useEffect(() => {
    if (!canvasRef.current) return;
    let destroyed = false;

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

        // === AUTONOMY: Disable mouse-driven interaction ===
        try {
          (model as any).autoInteract = false;
          if (model.internalModel?.motionManager) {
            (model.internalModel.motionManager as any).autoIdle = false;
          }
        } catch (_) {}

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

        // Parameter updates and animation binding are handled in requestAnimationFrame via the hook!
        // The autonomous expression loop runs inside useLive2DExpression hook at 60fps!

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
  const lastPlayedState = useRef<{ isThinking: boolean; emotion: string }>({ isThinking: false, emotion: '' });

  useEffect(() => {
    if (!modelRef.current) return;
    const model = modelRef.current;

    // Check if the state actually changed to prevent duplicate triggers
    if (
      lastPlayedState.current.isThinking === !!isThinking &&
      lastPlayedState.current.emotion === emotion
    ) {
      return;
    }

    lastPlayedState.current = { isThinking: !!isThinking, emotion };

    try {
      if (isThinking) {
        model.motion('Scene1');
      } else {
        const exprName = EMOTION_MAP[emotion] || 'idle';
        if (exprName === 'idle') {
          // Clear previous expression and run idle motion
          const expMgr = model.internalModel?.motionManager?.expressionManager;
          if (expMgr) expMgr.restoreExpression();
          model.motion('idle');
        } else {
          model.expression(exprName);
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
