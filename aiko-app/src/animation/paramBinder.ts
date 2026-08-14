/**
 * aiko-app/src/animation/paramBinder.ts
 * AAA Multi-Layer Animation Parameter Binder.
 * Dynamically binds Layer 1 (Idle), Layer 2 (Gaze Tracking), Layer 3 (Physics),
 * Layer 4 (Expression), Layer 5 (Lip-Sync), and Layer 6 (Gestures) into final
 * parameter values for the Live2D model each frame.
 */

import { ExpressionPreset } from './expressionBlender';
import { IdleOutputs } from './idleLayer';

export interface ParameterMetadata {
  id: string;
  min: number;
  max: number;
  defaultValue: number;
}

export class ParamBinder {
  private idMap: Map<string, string> = new Map();
  private metadata: Map<string, ParameterMetadata> = new Map();

  constructor(model: any) {
    this.refreshParameters(model);
  }

  public refreshParameters(model: any): void {
    this.idMap.clear();
    this.metadata.clear();

    if (!model) return;

    const params = model.internalModel?.parameters || [];
    params.forEach((p: any) => {
      if (p && typeof p.id === 'string') {
        const id = p.id;
        const lower = id.toLowerCase();
        this.idMap.set(lower, id);

        this.metadata.set(id, {
          id,
          min: typeof p.min === 'number' ? p.min : -30,
          max: typeof p.max === 'number' ? p.max : 30,
          defaultValue: typeof p.defaultValue === 'number' ? p.defaultValue : 0
        });
      }
    });

    console.log(`[ParamBinder] Registered ${this.idMap.size} Live2D parameters dynamically.`);
  }

  public getActualId(standardId: string): string | undefined {
    return this.idMap.get(standardId.toLowerCase());
  }

  public applyValue(coreModel: any, standardId: string, value: number): void {
    if (!coreModel) return;

    const actualId = this.getActualId(standardId);
    if (!actualId) return;

    const meta = this.metadata.get(actualId);
    if (meta) {
      value = Math.max(meta.min, Math.min(meta.max, value));
    }

    try {
      if (typeof coreModel.setParameterValueById === 'function') {
        coreModel.setParameterValueById(actualId, value);
      }
    } catch (_) {}
  }

  /**
   * Binds all 6 real-time animation layers onto the Live2D model core parameters.
   */
  public bind(
    coreModel: any,
    expression: ExpressionPreset,
    idle: IdleOutputs,
    gaze: { x: number; y: number },
    gestureOffsets: Record<string, number>,
    isTalking: boolean,
    mouthAmplitude: number
  ): void {
    if (!coreModel) return;

    // Helper to extract gesture offset safely
    const g = (id: string) => gestureOffsets[id] || 0;

    // 1. Head Angles (Yaw, Pitch, Roll) with Anatomical Clamping [-28, 28]
    // Layer 4 (Expression) + Layer 1 (Idle Sway) + Layer 2 (Gaze Target) + Layer 6 (Gesture)
    const rawAngleX = (expression.headTiltX * 15.0) + (gaze.x * 12.0) + idle.angleXOffset + g('ParamAngleX');
    const angleXVal = Math.max(-28.0, Math.min(28.0, rawAngleX));
    this.applyValue(coreModel, 'ParamAngleX', angleXVal);
    this.applyValue(coreModel, 'PARAM_ANGLE_X', angleXVal);

    const rawAngleY = (expression.headTiltY * 12.0) + (gaze.y * 10.0) + idle.angleYOffset + g('ParamAngleY');
    const angleYVal = Math.max(-28.0, Math.min(28.0, rawAngleY));
    this.applyValue(coreModel, 'ParamAngleY', angleYVal);
    this.applyValue(coreModel, 'PARAM_ANGLE_Y', angleYVal);

    const rawAngleZ = (expression.headTiltZ * 18.0) + idle.angleZOffset + g('ParamAngleZ');
    const angleZVal = Math.max(-28.0, Math.min(28.0, rawAngleZ));
    this.applyValue(coreModel, 'ParamAngleZ', angleZVal);
    this.applyValue(coreModel, 'PARAM_ANGLE_Z', angleZVal);

    // 2. Eyes Openness (Layer 4 Expression * Layer 1 Blink Offset + Gesture Offset)
    const eyeLVal = Math.max(0, (expression.eyeOpenness * idle.eyeLOpenOffset) + g('ParamEyeLOpen'));
    this.applyValue(coreModel, 'ParamEyeLOpen', eyeLVal);
    this.applyValue(coreModel, 'PARAM_EYE_L_OPEN', eyeLVal);

    const eyeRVal = Math.max(0, (expression.eyeOpenness * idle.eyeROpenOffset) + g('ParamEyeROpen'));
    this.applyValue(coreModel, 'ParamEyeROpen', eyeRVal);
    this.applyValue(coreModel, 'PARAM_EYE_R_OPEN', eyeRVal);

    // Eye Smile
    const eyeSmileVal = Math.max(0.0, (expression.eyeSmile || 0) + g('ParamEyeLSmile'));
    this.applyValue(coreModel, 'ParamEyeLSmile', eyeSmileVal);
    this.applyValue(coreModel, 'ParamEyeRSmile', eyeSmileVal);

    // Eye Ball Look Direction (Layer 2 Gaze + Layer 1 Saccade) [-0.8, 0.8]
    const eyeBallX = Math.max(-0.8, Math.min(0.8, (gaze.x * 0.7) + idle.eyeBallX));
    const eyeBallY = Math.max(-0.6, Math.min(0.6, (gaze.y * 0.6) + idle.eyeBallY));
    this.applyValue(coreModel, 'ParamEyeBallX', eyeBallX);
    this.applyValue(coreModel, 'PARAM_EYE_BALL_X', eyeBallX);
    this.applyValue(coreModel, 'ParamEyeBallY', eyeBallY);
    this.applyValue(coreModel, 'PARAM_EYE_BALL_Y', eyeBallY);

    // 3. Brows Position & Tension
    const browTension = expression.browTension + g('ParamBrowLY');
    this.applyValue(coreModel, 'ParamBrowLY', browTension);
    this.applyValue(coreModel, 'PARAM_BROW_L_Y', browTension);
    this.applyValue(coreModel, 'ParamBrowRY', browTension);
    this.applyValue(coreModel, 'PARAM_BROW_R_Y', browTension);

    // 4. Mouth Curves & Opening (Layer 5 Lip-Sync + Layer 4 Expression)
    const mouthForm = expression.mouthCurve + g('ParamMouthForm');
    this.applyValue(coreModel, 'ParamMouthForm', mouthForm);
    this.applyValue(coreModel, 'PARAM_MOUTH_FORM', mouthForm);

    // Lip sync attack/release amplitude blended with expression ambient mouthOpen
    const lipSyncMouthOpen = isTalking ? Math.min(1.0, mouthAmplitude * 1.6) : expression.mouthOpen;
    this.applyValue(coreModel, 'ParamMouthOpenY', lipSyncMouthOpen);
    this.applyValue(coreModel, 'PARAM_MOUTH_OPEN_Y', lipSyncMouthOpen);

    // 5. Body Sway (BodyAngleX/Y/Z)
    const bodyXVal = (expression.headTiltX * 6.0) + idle.bodyXOffset + g('ParamBodyAngleX');
    this.applyValue(coreModel, 'ParamBodyAngleX', bodyXVal);
    this.applyValue(coreModel, 'PARAM_BODY_ANGLE_X', bodyXVal);

    const bodyYVal = (expression.headTiltY * 4.0) + idle.bodyYOffset + g('ParamBodyAngleY');
    this.applyValue(coreModel, 'ParamBodyAngleY', bodyYVal);
    this.applyValue(coreModel, 'PARAM_BODY_ANGLE_Y', bodyYVal);

    const bodyZVal = (expression.headTiltZ * 5.0) + g('ParamBodyAngleZ');
    this.applyValue(coreModel, 'ParamBodyAngleZ', bodyZVal);
    this.applyValue(coreModel, 'PARAM_BODY_ANGLE_Z', bodyZVal);

    // 6. Breathing
    this.applyValue(coreModel, 'ParamBreath', idle.breathOffset);
    this.applyValue(coreModel, 'PARAM_BREATH', idle.breathOffset);

    // 7. Cheek Blush & Overlay Masks (Soft Vampirism Aesthetic)
    const totalBlush = Math.min(1.0, expression.blush + g('ParamCheek'));
    this.applyValue(coreModel, 'ParamCheek', totalBlush);
    this.applyValue(coreModel, 'PARAM_CHEEK', totalBlush);
    this.applyValue(coreModel, 'Param149', totalBlush); // Custom blush overlay

    if (expression.darkFace) {
      this.applyValue(coreModel, 'Param150', expression.darkFace); // Gloomy overlay
    } else {
      this.applyValue(coreModel, 'Param150', 0);
    }

    if (expression.cryTears || idle.tearLVal) {
      const tearAmount = expression.cryTears || idle.tearLVal;
      this.applyValue(coreModel, 'Param144', tearAmount);
      this.applyValue(coreModel, 'Param145', tearAmount);
      this.applyValue(coreModel, 'Param146', tearAmount);
    } else {
      this.applyValue(coreModel, 'Param144', 0);
      this.applyValue(coreModel, 'Param145', 0);
      this.applyValue(coreModel, 'Param146', 0);
    }

    // Boba & Jitter Wobble
    if (idle.bobaWobble) {
      this.applyValue(coreModel, 'Param148', idle.bobaWobble);
    }
  }
}
