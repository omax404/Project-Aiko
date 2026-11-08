/**
 * aiko-app/src/animation/paramBinder.ts
 * AAA Multi-Layer Animation Parameter Binder.
 * Dynamically binds Layer 1 (Idle), Layer 2 (Gaze Tracking), Layer 3 (Physics/Posture),
 * Layer 4 (Expression), Layer 5 (Lip-Sync + Vowel Formants), and Layer 6 (Gestures)
 * into final parameter values for the Live2D model each frame.
 */

import { ExpressionPreset } from './expressionBlender';
import { IdleOutputs } from './idleLayer';
import { MultiSpringController } from './springSmoother';

const BOUND_PARAMETER_IDS = [
  'ParamAngleX', 'PARAM_ANGLE_X', 'ParamAngleY', 'PARAM_ANGLE_Y', 'ParamAngleZ', 'PARAM_ANGLE_Z',
  'ParamEyeLOpen', 'PARAM_EYE_L_OPEN', 'ParamEyeROpen', 'PARAM_EYE_R_OPEN',
  'ParamEyeLSmile', 'ParamEyeRSmile', 'ParamEyeBallX', 'PARAM_EYE_BALL_X',
  'ParamEyeBallY', 'PARAM_EYE_BALL_Y', 'ParamBrowLY', 'PARAM_BROW_L_Y', 'ParamBrowRY', 'PARAM_BROW_R_Y',
  'ParamBrowLAngle', 'ParamBrowRAngle',
  'ParamMouthForm', 'PARAM_MOUTH_FORM', 'ParamMouthOpenY', 'PARAM_MOUTH_OPEN_Y',
  'ParamBodyAngleX', 'PARAM_BODY_ANGLE_X', 'ParamBodyAngleY', 'PARAM_BODY_ANGLE_Y',
  'ParamBodyAngleZ', 'PARAM_BODY_ANGLE_Z', 'ParamBreath', 'PARAM_BREATH',
  'ParamCheek', 'PARAM_CHEEK',
  'Paramqq', 'Param7', 'Param8', 'Param9', 'Param10', 'Param11', 'Param12', 'Param15',
  'Param149', 'Param150', 'Param144', 'Param145', 'Param146', 'Param148', 'Param132',
];

export interface ParameterMetadata {
  id: string;
  min: number;
  max: number;
  defaultValue: number;
}

export class ParamBinder {
  private idMap: Map<string, string> = new Map();
  private metadata: Map<string, ParameterMetadata> = new Map();
  private springs: MultiSpringController = new MultiSpringController();

  constructor(model: any) {
    // Register tuned critically-damped springs for each kinematic group
    this.springs.register('angleX', 0, 12);
    this.springs.register('angleY', 0, 12);
    this.springs.register('angleZ', 0, 10);
    this.springs.register('bodyX', 0, 8);
    this.springs.register('bodyY', 0, 8);
    this.springs.register('bodyZ', 0, 7);
    this.springs.register('eyeBallX', 0, 18);
    this.springs.register('eyeBallY', 0, 18);
    this.springs.register('browY', 0, 14);
    this.springs.register('mouthForm', 0.1, 16);
    this.springs.register('mouthOpen', 0, 22);
    this.springs.register('blush', 0, 8);
    this.springs.register('eyeSmile', 0, 12);
    this.springs.register('shoulderY', 0, 9);
    this.springs.register('hipX', 0, 7);
    this.springs.register('lean', 0, 6);
    this.refreshParameters(model);
  }

  public refreshParameters(model: any): void {
    this.idMap.clear();
    this.metadata.clear();

    if (!model) return;

    const coreModel = model.internalModel?.coreModel ?? model;
    if (typeof coreModel.getParameterIndex === 'function') {
      for (const id of BOUND_PARAMETER_IDS) {
        try {
          const index = coreModel.getParameterIndex(id);
          if (typeof index !== 'number' || index < 0) continue;

          this.idMap.set(id.toLowerCase(), id);
          this.metadata.set(id, {
            id,
            min: coreModel.getParameterMinimumValue?.(index) ?? -30,
            max: coreModel.getParameterMaximumValue?.(index) ?? 30,
            defaultValue: coreModel.getParameterDefaultValue?.(index) ?? 0,
          });
        } catch (_) {}
      }
    } else {
      // Keep compatibility with model wrappers that expose parameter objects.
      const params = model.internalModel?.parameters || [];
      if (Array.isArray(params)) {
        params.forEach((parameter: any) => {
          if (!parameter || typeof parameter.id !== 'string') return;
          const id = parameter.id;
          this.idMap.set(id.toLowerCase(), id);
          this.metadata.set(id, {
            id,
            min: typeof parameter.min === 'number' ? parameter.min : -30,
            max: typeof parameter.max === 'number' ? parameter.max : 30,
            defaultValue: typeof parameter.defaultValue === 'number' ? parameter.defaultValue : 0,
          });
        });
      }
    }
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
      } else if (typeof coreModel.getParameterIndex === 'function' && typeof coreModel.setParameterValueByIndex === 'function') {
        const index = coreModel.getParameterIndex(actualId);
        if (index >= 0) coreModel.setParameterValueByIndex(index, value);
      }
    } catch (_) {}
  }

  private smooth(key: string, target: number, dt?: number): number {
    if (typeof dt === 'number' && dt > 0) {
      return this.springs.update(key, target, dt);
    }
    this.springs.setVal(key, target);
    return target;
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
    mouthAmplitude: number,
    dt?: number,
    vowelFormOffset: number = 0
  ): void {
    if (!coreModel) return;

    const g = (id: string) => gestureOffsets[id] || 0;

    // 1. Head Angles (Yaw, Pitch, Roll) with Anatomical Clamping [-28, 28]
    const targetAngleX = Math.max(
      -28.0,
      Math.min(28.0, (expression.headTiltX * 15.0) + (gaze.x * 13.5) + idle.angleXOffset + g('ParamAngleX'))
    );
    const angleXVal = this.smooth('angleX', targetAngleX, dt);
    this.applyValue(coreModel, 'ParamAngleX', angleXVal);
    this.applyValue(coreModel, 'PARAM_ANGLE_X', angleXVal);

    const targetAngleY = Math.max(
      -28.0,
      Math.min(28.0, (expression.headTiltY * 12.0) + (gaze.y * 11.0) + idle.angleYOffset + g('ParamAngleY'))
    );
    const angleYVal = this.smooth('angleY', targetAngleY, dt);
    this.applyValue(coreModel, 'ParamAngleY', angleYVal);
    this.applyValue(coreModel, 'PARAM_ANGLE_Y', angleYVal);

    const targetAngleZ = Math.max(
      -28.0,
      Math.min(28.0, (expression.headTiltZ * 18.0) + (gaze.x * -2.5) + idle.angleZOffset + g('ParamAngleZ'))
    );
    const angleZVal = this.smooth('angleZ', targetAngleZ, dt);
    this.applyValue(coreModel, 'ParamAngleZ', angleZVal);
    this.applyValue(coreModel, 'PARAM_ANGLE_Z', angleZVal);

    // 2. Eyes Openness (Blink envelope directly modulates smoothed expression openness)
    const eyeLVal = Math.max(0, Math.min(1.25, (expression.eyeOpenness * idle.eyeLOpenOffset) + g('ParamEyeLOpen')));
    this.applyValue(coreModel, 'ParamEyeLOpen', eyeLVal);
    this.applyValue(coreModel, 'PARAM_EYE_L_OPEN', eyeLVal);

    const eyeRVal = Math.max(0, Math.min(1.25, (expression.eyeOpenness * idle.eyeROpenOffset) + g('ParamEyeROpen')));
    this.applyValue(coreModel, 'ParamEyeROpen', eyeRVal);
    this.applyValue(coreModel, 'PARAM_EYE_R_OPEN', eyeRVal);

    // Eye Smile (coupled gently with happy speech and blink squint)
    const blinkSquint = (1.0 - idle.eyeLOpenOffset) * 0.15;
    const targetEyeSmile = Math.max(0.0, Math.min(1.0, (expression.eyeSmile || 0) + blinkSquint + g('ParamEyeLSmile')));
    const eyeSmileVal = this.smooth('eyeSmile', targetEyeSmile, dt);
    this.applyValue(coreModel, 'ParamEyeLSmile', eyeSmileVal);
    this.applyValue(coreModel, 'ParamEyeRSmile', eyeSmileVal);

    // Eye Ball Look Direction (Layer 2 Gaze + Layer 1 Saccade) [-0.85, 0.85]
    const targetEyeBallX = Math.max(-0.85, Math.min(0.85, (gaze.x * 0.78) + idle.eyeBallX));
    const targetEyeBallY = Math.max(-0.65, Math.min(0.65, (gaze.y * 0.68) + idle.eyeBallY));
    const eyeBallX = this.smooth('eyeBallX', targetEyeBallX, dt);
    const eyeBallY = this.smooth('eyeBallY', targetEyeBallY, dt);
    this.applyValue(coreModel, 'ParamEyeBallX', eyeBallX);
    this.applyValue(coreModel, 'PARAM_EYE_BALL_X', eyeBallX);
    this.applyValue(coreModel, 'ParamEyeBallY', eyeBallY);
    this.applyValue(coreModel, 'PARAM_EYE_BALL_Y', eyeBallY);

    // 3. Brows Position & Angle
    const speechBrowLift = isTalking ? Math.min(0.22, mouthAmplitude * 0.28) : 0;
    const targetBrowY = Math.max(-1.0, Math.min(1.0, expression.browTension + speechBrowLift + g('ParamBrowLY')));
    const browTension = this.smooth('browY', targetBrowY, dt);
    this.applyValue(coreModel, 'ParamBrowLY', browTension);
    this.applyValue(coreModel, 'PARAM_BROW_L_Y', browTension);
    this.applyValue(coreModel, 'ParamBrowRY', browTension);
    this.applyValue(coreModel, 'PARAM_BROW_R_Y', browTension);
    this.applyValue(coreModel, 'ParamBrowLAngle', browTension * 0.65);
    this.applyValue(coreModel, 'ParamBrowRAngle', browTension * 0.65);

    // 4. Mouth Curves & Opening (Layer 5 Lip-Sync + Vowel Formant + Layer 4 Expression)
    const targetMouthForm = Math.max(
      -1.0,
      Math.min(1.0, expression.mouthCurve + (isTalking ? vowelFormOffset : 0) + g('ParamMouthForm'))
    );
    const mouthForm = this.smooth('mouthForm', targetMouthForm, dt);
    this.applyValue(coreModel, 'ParamMouthForm', mouthForm);
    this.applyValue(coreModel, 'PARAM_MOUTH_FORM', mouthForm);

    const targetMouthOpen = isTalking
      ? Math.max(expression.mouthOpen * 0.5, Math.min(1.0, mouthAmplitude * 1.6))
      : expression.mouthOpen;
    const lipSyncMouthOpen = this.smooth('mouthOpen', targetMouthOpen, dt);
    this.applyValue(coreModel, 'ParamMouthOpenY', lipSyncMouthOpen);
    this.applyValue(coreModel, 'PARAM_MOUTH_OPEN_Y', lipSyncMouthOpen);

    // Pout parameter for pouty expression
    const poutTarget = expression.name === 'pouty' ? 0.65 : 0;
    this.applyValue(coreModel, 'Param15', poutTarget);

    // 5. Body Sway & Secondary Kinematics (BodyAngleX/Y/Z, Shoulders, Hips, Forward Lean)
    const targetBodyX = (expression.headTiltX * 6.0) + (gaze.x * 3.5) + idle.bodyXOffset + g('ParamBodyAngleX');
    const bodyXVal = this.smooth('bodyX', targetBodyX, dt);
    this.applyValue(coreModel, 'ParamBodyAngleX', bodyXVal);
    this.applyValue(coreModel, 'PARAM_BODY_ANGLE_X', bodyXVal);

    const targetBodyY = (expression.headTiltY * 4.0) + (gaze.y * 2.2) + idle.bodyYOffset + g('ParamBodyAngleY');
    const bodyYVal = this.smooth('bodyY', targetBodyY, dt);
    this.applyValue(coreModel, 'ParamBodyAngleY', bodyYVal);
    this.applyValue(coreModel, 'PARAM_BODY_ANGLE_Y', bodyYVal);

    const targetBodyZ = (expression.headTiltZ * 5.0) + (idle.bodyZOffset ?? 0) + g('ParamBodyAngleZ');
    const bodyZVal = this.smooth('bodyZ', targetBodyZ, dt);
    this.applyValue(coreModel, 'ParamBodyAngleZ', bodyZVal);
    this.applyValue(coreModel, 'PARAM_BODY_ANGLE_Z', bodyZVal);

    // Shoulders & Hips secondary harmonic follow-through
    const shoulderY = this.smooth('shoulderY', idle.shoulderYOffset ?? (idle.breathOffset - 0.5), dt);
    const hipX = this.smooth('hipX', idle.hipXOffset ?? (-bodyXVal * 0.25), dt);
    const leanVal = this.smooth('lean', expression.name === 'happy' || expression.name === 'flirty' ? 0.35 : 0.1, dt);
    this.applyValue(coreModel, 'Param7', bodyXVal * 0.3);
    this.applyValue(coreModel, 'Param8', shoulderY);
    this.applyValue(coreModel, 'Param9', bodyZVal * 0.25);
    this.applyValue(coreModel, 'Param10', hipX);
    this.applyValue(coreModel, 'Param12', -bodyZVal * 0.2);
    this.applyValue(coreModel, 'Paramqq', leanVal);

    // 6. Breathing
    this.applyValue(coreModel, 'ParamBreath', idle.breathOffset);
    this.applyValue(coreModel, 'PARAM_BREATH', idle.breathOffset);

    // 7. Cheek Blush & Overlay Masks
    const targetBlush = Math.min(1.0, expression.blush + g('ParamCheek'));
    const totalBlush = this.smooth('blush', targetBlush, dt);
    this.applyValue(coreModel, 'ParamCheek', totalBlush);
    this.applyValue(coreModel, 'PARAM_CHEEK', totalBlush);
    this.applyValue(coreModel, 'Param149', totalBlush);

    if (expression.darkFace) {
      this.applyValue(coreModel, 'Param150', expression.darkFace);
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

    if (idle.bobaWobble) {
      this.applyValue(coreModel, 'Param148', idle.bobaWobble);
    }
  }
}
