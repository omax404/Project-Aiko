import React, { useEffect, useRef, useState } from 'react';

interface Live2DAvatarProps {
  modelUrl: string;
  isThinking?: boolean;
  isTalking?: boolean;
  emotion?: string;
  width?: number;
  height?: number;
  scale?: number;
  amplitude?: number;
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
}) => {
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

  // Keep track of props in refs to avoid re-running initialization effect
  useEffect(() => {
    animationState.current.isTalking = !!isTalking;
  }, [isTalking]);

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
          app.destroy(true);
          return;
        }

        modelRef.current = model;

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
        // Position perfectly in middle of canvas to avoid cutting
        model.position.set(width / 2, height / 2);

        app.stage.addChild(model);

        // Core animation loop
        app.ticker.add(() => {
          if (!modelRef.current) return;
          const delta = app.ticker.elapsedMS / 1000;
          const state = animationState.current;
          state.time += delta;
          
          const core = modelRef.current.internalModel?.coreModel;
          if (!core) return;

          // 1. Breathing (subtle vertical oscillation)
          const breathVal = (Math.sin(state.time * 1.5) * 0.5 + 0.5) * 0.015;
          try { core.setParameterValueById('ParamBodyAngleY', breathVal * 2); } catch(e){}

          // 2. Blinking
          state.blinkTimer += delta;
          if (state.blinkTimer >= state.nextBlink) {
            const blinkDuration = 0.15;
            const blinkProgress = (state.blinkTimer - state.nextBlink) / blinkDuration;
            if (blinkProgress < 1) {
              const blinkCurve = Math.sin(blinkProgress * Math.PI);
              const eyeClose = 1 - (blinkCurve * 0.95);
              try {
                core.setParameterValueById('ParamEyeLOpen', eyeClose);
                core.setParameterValueById('ParamEyeROpen', eyeClose);
              } catch(e){}
            } else {
              state.blinkTimer = 0;
              state.nextBlink = 2 + Math.random() * 4;
            }
          }

          // 3. Lip-Sync
          if (state.isTalking) {
            state.talkPhase += delta * 12;
            const mouthVal = (Math.sin(state.talkPhase) + 1) * 0.35 + (Math.sin(state.talkPhase * 1.7) + 1) * 0.15;
            try { core.setParameterValueById('ParamMouthOpenY', Math.min(1, mouthVal)); } catch(e){}
          } else {
            state.talkPhase = 0;
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
      try {
        appRef.current?.destroy(true, { children: true, texture: true, baseTexture: true });
      } catch (_) {}
      appRef.current = null;
      modelRef.current = null;
    };
  }, [modelUrl, width, height]);

  // Handle Dynamic Scaling without re-loading
  useEffect(() => {
    const model = modelRef.current;
    if (!model || !loaded) return;

    const modelW = model.internalModel.originalWidth;
    const modelH = model.internalModel.originalHeight;
    
    const scaleBaseX = (width * 0.95) / modelW;
    const scaleBaseY = (height * 0.95) / modelH;
    const finalScale = Math.min(scaleBaseX, scaleBaseY) * externalScale;

    model.scale.set(finalScale);
    
    // Adjust vertical position based on scale to keep upper body in focus when zoomed
    const vOffset = height * (0.1 + (externalScale - 1) * 0.15);
    model.position.set(width / 2, height / 2 + vOffset);
  }, [externalScale, loaded, width, height]);

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

  // SPECIAL PARAMETER ANIMATION (Reactive to specific keywords)
  useEffect(() => {
    const app = appRef.current;
    if (!app || !modelRef.current) return;

    const tickerCallback = () => {
        const core = modelRef.current?.internalModel?.coreModel;
        if (!core) return;
        const time = app.ticker.lastTime / 1000;

        // Custom Parameter Hooks
        try {
            // 1. Boba wobble if emotion is boba
            if (emotion === 'boba') {
                core.setParameterValueById('Param117', Math.sin(time * 10) * 15);
                core.setParameterValueById('Param119', Math.cos(time * 8) * 10);
            } else {
                core.setParameterValueById('Param117', 0);
                core.setParameterValueById('Param119', 0);
            }

            // 2. Tongue out if emotion is tongue
            if (emotion === 'tongue') {
                core.setParameterValueById('Param22', 1.0);
            } else {
                core.setParameterValueById('Param22', 0);
            }

            // 3. Pout if emotion is pout
            if (emotion === 'pout') {
                core.setParameterValueById('Param15', 1.0);
                core.setParameterValueById('Param16', 0.5); // Bloat cheeks slightly
            } else {
                core.setParameterValueById('Param15', 0);
                core.setParameterValueById('Param16', 0);
            }

            // 4. Blush (ParamCheek) if shy or romantic
            if (emotion === 'shy' || emotion === 'romantic') {
                core.setParameterValueById('ParamCheek', 0.8 + Math.sin(time * 2) * 0.2);
            } else {
                core.setParameterValueById('ParamCheek', 0);
            }

            // 5. Lip-sync (ParamMouthOpenY) based on amplitude
            if (isTalking && amplitude > 5) {
                // Normalize amplitude (0-100) to parameter range (0-1.5 approx)
                const mouthOpen = Math.min((amplitude / 60), 1.0); 
                core.setParameterValueById('ParamMouthOpenY', mouthOpen);
                core.setParameterValueById('ParamMouthForm', Math.sin(time * 8) * 0.2); 
            }
        } catch(e) {}
    };

    app.ticker.add(tickerCallback);
    return () => app.ticker.remove(tickerCallback);
  }, [emotion, loaded]);

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
                className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        </div>
      )}
      <canvas
        ref={canvasRef}
        className="pointer-events-none"
        style={{ opacity: loaded ? 1 : 0, transition: 'opacity 0.5s ease' }}
      />
    </div>
  );
};
