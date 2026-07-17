import { ExpressionTargets } from './emotionMapper';
import { IdleOutputs } from './idleLayer';

export interface ParameterMetadata {
  id: string;
  min: number;
  max: number;
  defaultValue: number;
}

/**
 * Handles dynamic discovery, case-insensitive mapping, clamping, and binding
 * of targets + idle layers to the Live2D model core parameters.
 */
export class ParamBinder {
  private idMap: Map<string, string> = new Map();
  private metadata: Map<string, ParameterMetadata> = new Map();

  constructor(model: any) {
    this.refreshParameters(model);
  }

  /**
   * Refreshes the internal parameter lookup tables from the loaded model structure.
   */
  public refreshParameters(model: any): void {
    this.idMap.clear();
    this.metadata.clear();

    if (!model) return;

    // Discover parameters from pixi-live2d-display internal list
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

    console.log(`[ParamBinder] Registered ${this.idMap.size} parameters dynamically from model.`);
  }

  /**
   * Finds the actual ID of a parameter case-insensitively, e.g. "ParamAngleX" or "PARAM_ANGLE_X".
   */
  public getActualId(standardId: string): string | undefined {
    return this.idMap.get(standardId.toLowerCase());
  }

  /**
   * Clamps and applies a value to a parameter by its standard ID safely.
   */
  public applyValue(coreModel: any, standardId: string, value: number): void {
    if (!coreModel) return;

    const actualId = this.getActualId(standardId);
    if (!actualId) return; // Fallback: parameter does not exist on this model

    const meta = this.metadata.get(actualId);
    if (meta) {
      // Respect model boundaries strictly
      value = Math.max(meta.min, Math.min(meta.max, value));
    }

    try {
      if (typeof coreModel.setParameterValueById === 'function') {
        coreModel.setParameterValueById(actualId, value);
      }
    } catch (e) {
      console.warn(`[ParamBinder] Failed to set parameter ${actualId} to ${value}:`, e);
    }
  }

  /**
   * Binds targets and idle offsets onto the model's core parameters.
   */
  public bind(
    coreModel: any,
    targets: ExpressionTargets,
    idle: IdleOutputs,
    isTalking: boolean,
    mouthAmplitude: number,
    cortisol: number,
    adrenaline: number
  ): void {
    if (!coreModel) return;

    // 1. Head Angles (Yaw, Pitch, Roll)
    // AngleX: X range is typically [-30, 30]
    const angleXVal = targets.headTiltX * 28.0 + idle.angleXOffset;
    this.applyValue(coreModel, 'ParamAngleX', angleXVal);
    this.applyValue(coreModel, 'PARAM_ANGLE_X', angleXVal);

    // AngleY: Y range is typically [-30, 30]
    const angleYVal = targets.headTiltY * 20.0 + idle.angleYOffset;
    this.applyValue(coreModel, 'ParamAngleY', angleYVal);
    this.applyValue(coreModel, 'PARAM_ANGLE_Y', angleYVal);

    // AngleZ: Z range is typically [-30, 30]
    const angleZVal = targets.headTiltZ * 24.0 + idle.angleZOffset;
    this.applyValue(coreModel, 'ParamAngleZ', angleZVal);
    this.applyValue(coreModel, 'PARAM_ANGLE_Z', angleZVal);

    // 2. Eyes Openness (Left & Right)
    // Multiply base target openness by blink state coefficient
    const eyeLVal = targets.eyeOpenness * idle.eyeLOpenOffset;
    this.applyValue(coreModel, 'ParamEyeLOpen', eyeLVal);
    this.applyValue(coreModel, 'PARAM_EYE_L_OPEN', eyeLVal);

    const eyeRVal = targets.eyeOpenness * idle.eyeROpenOffset;
    this.applyValue(coreModel, 'ParamEyeROpen', eyeRVal);
    this.applyValue(coreModel, 'PARAM_EYE_R_OPEN', eyeRVal);

    // Eye Smile (makes eyes crinkle on happiness)
    const eyeSmileVal = Math.max(0.0, targets.mouthCurve);
    this.applyValue(coreModel, 'ParamEyeLSmile', eyeSmileVal);
    this.applyValue(coreModel, 'ParamEyeRSmile', eyeSmileVal);

    // Eye Look Direction (EyeBall X / Y)
    this.applyValue(coreModel, 'ParamEyeBallX', idle.eyeBallX);
    this.applyValue(coreModel, 'PARAM_EYE_BALL_X', idle.eyeBallX);
    this.applyValue(coreModel, 'ParamEyeBallY', idle.eyeBallY);
    this.applyValue(coreModel, 'PARAM_EYE_BALL_Y', idle.eyeBallY);

    // 3. Brows Vertical Position (Left & Right)
    this.applyValue(coreModel, 'ParamBrowLY', targets.browTension);
    this.applyValue(coreModel, 'PARAM_BROW_L_Y', targets.browTension);
    this.applyValue(coreModel, 'ParamBrowRY', targets.browTension);
    this.applyValue(coreModel, 'PARAM_BROW_R_Y', targets.browTension);

    // 4. Mouth Curves & Opening
    // Mouth Form (-1 is sad frown, 1 is happy smile)
    this.applyValue(coreModel, 'ParamMouthForm', targets.mouthCurve);
    this.applyValue(coreModel, 'PARAM_MOUTH_FORM', targets.mouthCurve);

    // Mouth Open (speech amplitude has priority override, otherwise ambient mouthOpen)
    const mouthOpenVal = isTalking ? Math.min(1.0, mouthAmplitude * 1.5) : targets.mouthOpen;
    this.applyValue(coreModel, 'ParamMouthOpenY', mouthOpenVal);
    this.applyValue(coreModel, 'PARAM_MOUTH_OPEN_Y', mouthOpenVal);

    // 5. Body Sway (BodyAngleX/Y/Z)
    const bodyXVal = targets.bodySway * 10.0;
    this.applyValue(coreModel, 'ParamBodyAngleX', bodyXVal);
    this.applyValue(coreModel, 'PARAM_BODY_ANGLE_X', bodyXVal);
    
    const bodyYVal = targets.headTiltY * 3.5;
    this.applyValue(coreModel, 'ParamBodyAngleY', bodyYVal);
    this.applyValue(coreModel, 'PARAM_BODY_ANGLE_Y', bodyYVal);

    const bodyZVal = targets.headTiltZ * 4.0;
    this.applyValue(coreModel, 'ParamBodyAngleZ', bodyZVal);
    this.applyValue(coreModel, 'PARAM_BODY_ANGLE_Z', bodyZVal);

    // 6. Breathing
    this.applyValue(coreModel, 'ParamBreath', idle.breathOffset);
    this.applyValue(coreModel, 'PARAM_BREATH', idle.breathOffset);

    // 7. Cheek Blush
    this.applyValue(coreModel, 'ParamCheek', targets.blush);
    this.applyValue(coreModel, 'PARAM_CHEEK', targets.blush);
    this.applyValue(coreModel, 'Param149', targets.blush); // Custom Aiko blush overlay id

    // 8. Custom model parameters (Blushing, Tears, Panic jitters, Wobble)
    if (idle.jitterVal !== 0) {
      this.applyValue(coreModel, 'Param141', 0.5 + idle.jitterVal); // Jitter 1
      this.applyValue(coreModel, 'Param142', 0.5 + Math.cos(idle.jitterVal * 15) * 0.1); // Jitter 2
      this.applyValue(coreModel, 'Param132', Math.max(cortisol, adrenaline)); // Jitter state
    } else {
      this.applyValue(coreModel, 'Param141', 0);
      this.applyValue(coreModel, 'Param142', 0);
      this.applyValue(coreModel, 'Param132', 0);
    }

    if (idle.tearLVal !== 0 || idle.tearRVal !== 0) {
      this.applyValue(coreModel, 'Param144', cortisol); // Crying state
      this.applyValue(coreModel, 'Param145', idle.tearLVal); // Teardrop 1
      this.applyValue(coreModel, 'Param146', idle.tearRVal); // Teardrop 2
    } else {
      this.applyValue(coreModel, 'Param144', 0);
      this.applyValue(coreModel, 'Param145', 0);
      this.applyValue(coreModel, 'Param146', 0);
    }

    if (idle.bobaWobble !== 0) {
      this.applyValue(coreModel, 'Param148', idle.bobaWobble); // Wobble parameter
      this.applyValue(coreModel, 'Param15', idle.bobaWobble * 0.8); // Custom pout/shake sway
    } else {
      this.applyValue(coreModel, 'Param148', 0);
      this.applyValue(coreModel, 'Param15', 0);
    }
  }
}
