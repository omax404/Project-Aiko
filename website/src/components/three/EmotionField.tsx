"use client";

import { useMemo, useRef, useEffect, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { useEmotion } from "@/components/providers/EmotionProvider";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { useMediaQuery } from "@/hooks/useMediaQuery";

const COUNT = 2200;

function Particles() {
  const { config } = useEmotion();
  const points = useRef<THREE.Points>(null);
  const material = useRef<THREE.ShaderMaterial>(null);
  const target = useRef({
    dopamine: config.neuromodulators.dopamine,
    serotonin: config.neuromodulators.serotonin,
    cortisol: config.neuromodulators.cortisol,
    adrenaline: config.neuromodulators.adrenaline,
    color: new THREE.Color(config.color),
    secondary: new THREE.Color(config.secondary),
  });

  const { positions, seeds, phases } = useMemo(() => {
    const positions = new Float32Array(COUNT * 3);
    const seeds = new Float32Array(COUNT);
    const phases = new Float32Array(COUNT);
    for (let i = 0; i < COUNT; i++) {
      const r = Math.pow(Math.random(), 0.55) * 4.2;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta) * 0.72;
      positions[i * 3 + 2] = r * Math.cos(phi) * 0.85;
      seeds[i] = Math.random();
      phases[i] = Math.random() * Math.PI * 2;
    }
    return { positions, seeds, phases };
  }, []);

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uDopamine: { value: 0.35 },
      uSerotonin: { value: 0.7 },
      uCortisol: { value: 0.15 },
      uAdrenaline: { value: 0.1 },
      uColorA: { value: new THREE.Color(config.color) },
      uColorB: { value: new THREE.Color(config.secondary) },
      uPixelRatio: {
        value: typeof window !== "undefined" ? Math.min(window.devicePixelRatio, 2) : 1,
      },
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  useEffect(() => {
    target.current.dopamine = config.neuromodulators.dopamine;
    target.current.serotonin = config.neuromodulators.serotonin;
    target.current.cortisol = config.neuromodulators.cortisol;
    target.current.adrenaline = config.neuromodulators.adrenaline;
    target.current.color.set(config.color);
    target.current.secondary.set(config.secondary);
  }, [config]);

  useFrame((state, delta) => {
    if (!material.current) return;
    const u = material.current.uniforms;
    const t = target.current;
    const lerp = 1 - Math.exp(-2.4 * delta);

    u.uTime.value = state.clock.elapsedTime;
    u.uDopamine.value += (t.dopamine - u.uDopamine.value) * lerp;
    u.uSerotonin.value += (t.serotonin - u.uSerotonin.value) * lerp;
    u.uCortisol.value += (t.cortisol - u.uCortisol.value) * lerp;
    u.uAdrenaline.value += (t.adrenaline - u.uAdrenaline.value) * lerp;
    (u.uColorA.value as THREE.Color).lerp(t.color, lerp);
    (u.uColorB.value as THREE.Color).lerp(t.secondary, lerp);

    if (points.current) {
      points.current.rotation.y += delta * (0.04 + u.uAdrenaline.value * 0.12);
      points.current.rotation.x =
        Math.sin(state.clock.elapsedTime * 0.15) * 0.08 +
        u.uCortisol.value * 0.05;
    }
  });

  return (
    <points ref={points} frustumCulled={false}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-aSeed" args={[seeds, 1]} />
        <bufferAttribute attach="attributes-aPhase" args={[phases, 1]} />
      </bufferGeometry>
      <shaderMaterial
        ref={material}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        uniforms={uniforms}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
      />
    </points>
  );
}

const vertexShader = /* glsl */ `
  attribute float aSeed;
  attribute float aPhase;
  uniform float uTime;
  uniform float uDopamine;
  uniform float uSerotonin;
  uniform float uCortisol;
  uniform float uAdrenaline;
  uniform float uPixelRatio;
  varying float vAlpha;
  varying float vMix;

  void main() {
    vec3 pos = position;
    float t = uTime;

    // Serotonin: smooth orbital drift
    float calm = uSerotonin * 0.35;
    pos.x += sin(t * (0.3 + aSeed * 0.4) + aPhase) * calm * (0.4 + aSeed);
    pos.y += cos(t * (0.25 + aSeed * 0.35) + aPhase * 1.3) * calm * 0.5;

    // Dopamine: outward bloom / expansion
    float expand = 1.0 + uDopamine * 0.35 * (0.5 + aSeed * 0.5);
    pos *= expand;

    // Cortisol: jitter / noise
    float j = uCortisol * 0.22;
    pos.x += sin(t * 8.0 + aPhase * 20.0) * j * aSeed;
    pos.y += cos(t * 9.5 + aPhase * 17.0) * j * (1.0 - aSeed);
    pos.z += sin(t * 7.0 + aSeed * 30.0) * j * 0.6;

    // Adrenaline: rapid pulse toward center then out
    float pulse = sin(t * (2.5 + uAdrenaline * 4.0) + aPhase) * uAdrenaline * 0.18;
    pos *= 1.0 + pulse;

    // Focus clustering (low serotonin + high dopamine = tighter shell mid-ring)
    float cluster = mix(1.0, 0.72 + aSeed * 0.35, clamp(uDopamine - uSerotonin * 0.3, 0.0, 1.0) * 0.5);
    pos *= cluster;

    vec4 mv = modelViewMatrix * vec4(pos, 1.0);
    gl_Position = projectionMatrix * mv;

    float size = (2.2 + uDopamine * 2.8 - uCortisol * 0.8) * (0.55 + aSeed * 0.9);
    size *= (300.0 / -mv.z);
    gl_PointSize = size * uPixelRatio;

    vAlpha = 0.25 + uSerotonin * 0.35 + uDopamine * 0.2 - uCortisol * 0.1;
    vAlpha *= smoothstep(5.5, 1.2, length(pos));
    vMix = aSeed;
  }
`;

const fragmentShader = /* glsl */ `
  uniform vec3 uColorA;
  uniform vec3 uColorB;
  uniform float uAdrenaline;
  varying float vAlpha;
  varying float vMix;

  void main() {
    vec2 uv = gl_PointCoord - 0.5;
    float d = length(uv);
    if (d > 0.5) discard;

    float core = smoothstep(0.5, 0.0, d);
    float halo = smoothstep(0.5, 0.15, d);
    vec3 col = mix(uColorA, uColorB, vMix);
    col += uAdrenaline * 0.15;

    float alpha = (core * 0.9 + halo * 0.35) * vAlpha;
    gl_FragColor = vec4(col, alpha);
  }
`;

function Scene() {
  return (
    <>
      <color attach="background" args={["#000000"]} />
      <Particles />
      <ambientLight intensity={0.2} />
    </>
  );
}

export function EmotionField({ className = "" }: { className?: string }) {
  const reduced = useReducedMotion();
  const isMobile = useMediaQuery("(max-width: 768px)");
  const { config } = useEmotion();

  if (reduced) {
    return (
      <div
        className={`absolute inset-0 ${className}`}
        style={{
          background: `radial-gradient(ellipse at 50% 45%, ${config.color}33 0%, transparent 60%)`,
        }}
        aria-hidden
      />
    );
  }

  return (
    <div className={`absolute inset-0 ${className}`} aria-hidden>
      <Canvas
        dpr={[1, isMobile ? 1.25 : 1.75]}
        camera={{ position: [0, 0, 7.5], fov: 50, near: 0.1, far: 40 }}
        gl={{
          antialias: false,
          alpha: true,
          powerPreference: "high-performance",
        }}
        style={{ background: "transparent" }}
      >
        <Suspense fallback={null}>
          <Scene />
        </Suspense>
      </Canvas>
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background: `
            radial-gradient(ellipse 55% 50% at 50% 48%, transparent 20%, rgba(11,8,16,0.35) 55%, rgba(11,8,16,0.85) 100%),
            radial-gradient(ellipse 80% 60% at 50% 100%, rgba(11,8,16,0.9), transparent 50%)
          `,
        }}
      />
    </div>
  );
}
