"use client";

import dynamic from "next/dynamic";
import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";
import { MagneticButton } from "@/components/ui/MagneticButton";
import { useEmotion } from "@/components/providers/EmotionProvider";
import { emotions, site, type EmotionKey } from "@/lib/content";
import { cn } from "@/lib/cn";
import { useReducedMotion } from "@/hooks/useReducedMotion";

const EmotionField = dynamic(
  () =>
    import("@/components/three/EmotionField").then((m) => m.EmotionField),
  { ssr: false },
);

const EMOTION_KEYS = Object.keys(emotions) as EmotionKey[];

export function Hero() {
  const ref = useRef<HTMLElement>(null);
  const { emotion, setEmotion, config } = useEmotion();
  const reduced = useReducedMotion();
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const yText = useTransform(scrollYProgress, [0, 1], [0, reduced ? 0 : 120]);
  const opacity = useTransform(scrollYProgress, [0, 0.7], [1, 0]);
  const scaleField = useTransform(scrollYProgress, [0, 1], [1, reduced ? 1 : 1.15]);

  return (
    <section
      id="top"
      ref={ref}
      className="relative flex min-h-[100svh] flex-col justify-end overflow-hidden pb-16 pt-28 sm:pb-24 sm:pt-32"
    >
      {/* Signature moment */}
      <motion.div className="absolute inset-0 z-0" style={{ scale: scaleField }}>
        <EmotionField />
      </motion.div>

      {/* Ambient orbs */}
      <div
        className="pointer-events-none absolute top-1/4 left-1/2 z-[1] h-[40vmax] w-[40vmax] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-30 blur-[100px] transition-colors duration-1000"
        style={{ background: config.color }}
        aria-hidden
      />

      <motion.div
        style={{ y: yText, opacity }}
        className="section-pad relative z-10 mx-auto w-full max-w-6xl"
      >
        <motion.div
          initial={reduced ? false : { opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
          className="mb-6 inline-flex items-center gap-2 rounded-full border border-glass-border bg-plum/50 px-3 py-1.5 backdrop-blur-md"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-bloom shadow-[0_0_8px_var(--bloom)]" />
          <span className="text-[11px] font-medium tracking-[0.16em] text-lavender uppercase">
            Self-hosted · You-owned · Open source
          </span>
        </motion.div>

        <motion.h1
          initial={reduced ? false : { opacity: 0, y: 48 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.05, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
          className="text-display max-w-4xl text-[clamp(2.75rem,8vw,5.75rem)] text-ink"
        >
          She doesn&apos;t just chat.
          <br />
          <span
            className="bg-clip-text text-transparent transition-all duration-700"
            style={{
              backgroundImage: `linear-gradient(120deg, ${config.secondary}, ${config.color}, var(--bloom))`,
            }}
          >
            She feels.
          </span>
        </motion.h1>

        <motion.p
          initial={reduced ? false : { opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.95, ease: [0.16, 1, 0.3, 1], delay: 0.35 }}
          className="text-body mt-6 max-w-xl text-base sm:text-lg"
        >
          {site.description}
        </motion.p>

        <motion.div
          initial={reduced ? false : { opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1], delay: 0.48 }}
          className="mt-8 flex flex-wrap items-center gap-3"
        >
          <MagneticButton href="#quickstart" variant="primary">
            Wake her up
            <ArrowIcon />
          </MagneticButton>
          <MagneticButton href={site.github} variant="ghost">
            View on GitHub
          </MagneticButton>
        </motion.div>

        {/* Emotion state control — drives the particle field */}
        <motion.div
          initial={reduced ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1], delay: 0.6 }}
          className="mt-12 max-w-xl"
        >
          <div className="mb-3 flex items-end justify-between gap-4">
            <div>
              <p className="text-[10px] tracking-[0.2em] text-lavender/80 uppercase">
                Neuromodulator field
              </p>
              <p className="text-sm text-mist">
                <span className="text-lavender">{config.label}</span>
                <span className="text-muted"> — {config.description}</span>
              </p>
            </div>
          </div>

          <div
            className="flex flex-wrap gap-1.5"
            role="tablist"
            aria-label="Emotional state"
          >
            {EMOTION_KEYS.map((key) => (
              <button
                key={key}
                type="button"
                role="tab"
                aria-selected={emotion === key}
                onClick={() => setEmotion(key)}
                className={cn(
                  "rounded-full border px-3 py-1.5 text-xs transition-all duration-300",
                  emotion === key
                    ? "border-transparent text-void"
                    : "border-glass-border bg-void/40 text-muted hover:border-lavender/30 hover:text-mist",
                )}
                style={
                  emotion === key
                    ? { background: emotions[key].color }
                    : undefined
                }
                data-cursor
                data-cursor-label={emotions[key].label}
              >
                {emotions[key].label}
              </button>
            ))}
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {(
              Object.entries(config.neuromodulators) as [
                string,
                number,
              ][]
            ).map(([name, value]) => (
              <div key={name}>
                <div className="mb-1 flex justify-between text-[10px] tracking-wide text-muted uppercase">
                  <span>{name}</span>
                  <span className="font-mono text-lavender/80">
                    {Math.round(value * 100)}
                  </span>
                </div>
                <div className="neuro-bar">
                  <span
                    style={{
                      width: `${value * 100}%`,
                      background: `linear-gradient(90deg, ${config.color}, ${config.secondary})`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </motion.div>

      {/* Scroll hint */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.4 }}
        className="absolute bottom-6 left-1/2 z-10 hidden -translate-x-1/2 flex-col items-center gap-2 sm:flex"
        aria-hidden
      >
        <span className="text-[10px] tracking-[0.25em] text-muted uppercase">
          Scroll
        </span>
        <span className="h-8 w-px bg-gradient-to-b from-lavender/60 to-transparent" />
      </motion.div>
    </section>
  );
}

function ArrowIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M5 12h14M13 6l6 6-6 6"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
