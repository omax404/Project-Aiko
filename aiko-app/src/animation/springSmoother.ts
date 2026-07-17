/**
 * Critically-damped spring smoothing system for frame-rate independent physics-based easing.
 * Uses the analytical solution of the equation of motion for a critically damped spring
 * to guarantee stability and prevent overshoot/explosions at high time steps.
 */
export interface SpringConfig {
  stiffness: number; // Angular frequency omega (typically 5 to 25)
}

export class Spring {
  private current: number = 0;
  private velocity: number = 0;
  private config: SpringConfig;

  constructor(initialValue: number, config: SpringConfig = { stiffness: 10 }) {
    this.current = initialValue;
    this.config = config;
  }

  /**
   * Updates the spring towards the target value.
   * @param target The target value to ease towards.
   * @param dt Delta time in seconds since the last frame.
   */
  public update(target: number, dt: number): number {
    if (dt <= 0) return this.current;
    
    const omega = this.config.stiffness;
    const x0 = this.current - target;
    const v0 = this.velocity;
    
    const expTerm = Math.exp(-omega * dt);
    const constantTerm = v0 + omega * x0;
    
    this.current = (x0 + constantTerm * dt) * expTerm + target;
    this.velocity = (v0 - omega * constantTerm * dt) * expTerm;
    
    // Prevent micro-drift floating point precision issues
    if (Math.abs(this.current - target) < 1e-6 && Math.abs(this.velocity) < 1e-6) {
      this.current = target;
      this.velocity = 0;
    }
    
    return this.current;
  }

  public getVal(): number {
    return this.current;
  }

  public setVal(val: number): void {
    this.current = val;
    this.velocity = 0;
  }
}

/**
 * Controller for managing multiple springs for separate expression channels.
 */
export class MultiSpringController {
  private springs: Map<string, Spring> = new Map();

  public register(key: string, initialValue: number, stiffness: number): void {
    this.springs.set(key, new Spring(initialValue, { stiffness }));
  }

  public update(key: string, target: number, dt: number): number {
    const spring = this.springs.get(key);
    if (!spring) {
      this.register(key, target, 10);
      return target;
    }
    return spring.update(target, dt);
  }

  public getVal(key: string): number {
    return this.springs.get(key)?.getVal() ?? 0;
  }
  
  public setVal(key: string, val: number): void {
    this.springs.get(key)?.setVal(val);
  }
}
