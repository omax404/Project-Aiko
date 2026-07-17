"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence, useScroll, useMotionValueEvent } from "framer-motion";
import { capabilities, platforms, providers, desktopFeatures } from "@/lib/content";
import { SectionReveal } from "@/components/ui/SectionReveal";
import { GlassCard } from "@/components/ui/GlassCard";
import { cn } from "@/lib/cn";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { useMediaQuery } from "@/hooks/useMediaQuery";

export function Capabilities() {
  const [active, setActive] = useState(0);
  const reduced = useReducedMotion();
  const isDesktop = useMediaQuery("(min-width: 1024px)");
  const containerRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Scroll-synced tabs on desktop
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start center", "end center"],
  });

  useMotionValueEvent(scrollYProgress, "change", (v) => {
    if (!isDesktop || reduced) return;
    const idx = Math.min(
      capabilities.length - 1,
      Math.max(0, Math.floor(v * capabilities.length)),
    );
    setActive(idx);
  });

  useEffect(() => {
    if (isDesktop) return;
    // no-op; mobile uses click tabs
  }, [isDesktop]);

  const current = capabilities[active];

  return (
    <section id="capabilities" className="section-y section-pad relative">
      <div className="mx-auto max-w-6xl">
        <SectionReveal>
          <div className="mb-12 max-w-2xl">
            <p className="mb-3 text-xs font-medium tracking-[0.22em] text-lavender uppercase">
              Core systems
            </p>
            <h2 className="text-display text-4xl text-ink sm:text-5xl">
              Six systems.
              <span className="block text-muted">One companion.</span>
            </h2>
          </div>
        </SectionReveal>

        <div
          ref={containerRef}
          className="lg:grid lg:grid-cols-[240px_1fr] lg:gap-10"
        >
          {/* Tabs */}
          <div className="mb-6 lg:mb-0">
            <div
              className="flex gap-2 overflow-x-auto pb-2 lg:sticky lg:top-28 lg:flex-col lg:overflow-visible lg:pb-0"
              role="tablist"
              aria-label="Core systems"
            >
              {capabilities.map((cap, i) => (
                <button
                  key={cap.id}
                  type="button"
                  role="tab"
                  aria-selected={active === i}
                  onClick={() => {
                    setActive(i);
                    if (isDesktop && itemRefs.current[i]) {
                      itemRefs.current[i]?.scrollIntoView({
                        behavior: reduced ? "auto" : "smooth",
                        block: "center",
                      });
                    }
                  }}
                  className={cn(
                    "group relative flex shrink-0 items-center gap-2.5 rounded-xl border px-3.5 py-2.5 text-left transition-all duration-300 lg:w-full",
                    active === i
                      ? "border-lavender/35 bg-lavender/10 text-mist"
                      : "border-transparent text-muted hover:border-glass-border hover:bg-plum/40 hover:text-mist",
                  )}
                  data-cursor
                >
                  <span className="text-base" aria-hidden>
                    {cap.icon}
                  </span>
                  <span className="text-sm font-medium">{cap.label}</span>
                  {active === i && (
                    <motion.span
                      layoutId="cap-indicator"
                      className="absolute top-1/2 right-2.5 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-lavender"
                    />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Content panel + scroll anchors */}
          <div>
            {/* Sticky detail card (always shows active) */}
            <div className="lg:sticky lg:top-28">
              <AnimatePresence mode="wait">
                <motion.div
                  key={current.id}
                  initial={reduced ? false : { opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={reduced ? undefined : { opacity: 0, y: -12 }}
                  transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                >
                  <GlassCard className="p-6 sm:p-8" glow>
                    <div className="mb-1 flex items-center gap-3">
                      <span className="text-2xl" aria-hidden>
                        {current.icon}
                      </span>
                      <p className="text-xs tracking-[0.18em] text-lavender uppercase">
                        {current.label}
                      </p>
                    </div>
                    <h3 className="text-display mt-2 text-2xl text-ink sm:text-3xl">
                      {current.title}
                    </h3>
                    <p className="text-body mt-3 text-base">{current.summary}</p>
                    <ul className="mt-6 space-y-3">
                      {current.points.map((point) => (
                        <li
                          key={point}
                          className="flex gap-3 text-sm text-mist"
                        >
                          <span
                            className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-lavender"
                            aria-hidden
                          />
                          {point}
                        </li>
                      ))}
                    </ul>
                  </GlassCard>
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Invisible scroll drivers for desktop sticky sync */}
            <div className="pointer-events-none hidden lg:block" aria-hidden>
              {capabilities.map((cap, i) => (
                <div
                  key={cap.id}
                  ref={(el) => {
                    itemRefs.current[i] = el;
                  }}
                  className="h-[40vh]"
                />
              ))}
            </div>
          </div>
        </div>

        {/* Platforms */}
        <SectionReveal delay={0.1}>
          <div className="mt-20">
            <p className="mb-6 text-xs font-medium tracking-[0.22em] text-lavender uppercase">
              Platforms
            </p>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {platforms.map((p) => (
                <GlassCard key={p.name} className="p-5">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="rounded-full bg-lavender/15 px-2 py-0.5 text-[10px] font-medium tracking-wide text-lavender uppercase">
                      {p.status}
                    </span>
                  </div>
                  <h3 className="text-sm font-medium text-ink">{p.name}</h3>
                  <p className="mt-1 text-xs text-muted">{p.detail}</p>
                </GlassCard>
              ))}
            </div>
          </div>
        </SectionReveal>

        {/* Desktop overlay features */}
        <SectionReveal delay={0.12}>
          <div className="mt-10 overflow-hidden rounded-2xl border border-glass-border bg-gradient-to-br from-midnight/80 to-plum/40 p-6 sm:p-8">
            <div className="grid gap-8 lg:grid-cols-[1fr_1.2fr] lg:items-center">
              <div>
                <p className="text-xs tracking-[0.18em] text-lavender uppercase">
                  Tauri Desktop Overlay
                </p>
                <h3 className="text-display mt-2 text-2xl text-ink sm:text-3xl">
                  Always nearby.
                  <br />
                  Never in the way.
                </h3>
                <p className="text-body mt-3 text-sm">
                  Pixel-perfect click-through, Live2D driven by live emotional
                  state, and a unified dashboard for chat, stats, and project
                  intelligence.
                </p>
              </div>
              <ul className="space-y-3">
                {desktopFeatures.map((f) => (
                  <li
                    key={f.title}
                    className="flex gap-3 rounded-xl border border-glass-border bg-void/40 px-4 py-3"
                  >
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-bloom" />
                    <div>
                      <p className="text-sm font-medium text-mist">{f.title}</p>
                      <p className="text-xs text-muted">{f.detail}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </SectionReveal>

        {/* Providers */}
        <SectionReveal delay={0.1}>
          <div className="mt-16">
            <p className="mb-2 text-xs font-medium tracking-[0.22em] text-lavender uppercase">
              Providers
            </p>
            <p className="text-body mb-6 max-w-xl text-sm">
              Any OpenAI-compatible API. Ollama by default. Swap models in
              Settings — Save & Apply takes effect instantly.
            </p>
            <div className="flex flex-wrap gap-2">
              {providers.map((p) => (
                <div
                  key={p.name}
                  className="group rounded-full border border-glass-border bg-plum/40 px-3.5 py-2 transition-colors hover:border-lavender/30"
                  data-cursor
                  data-cursor-label={p.model}
                >
                  <span className="text-xs font-medium text-mist">{p.name}</span>
                  <span className="mx-1.5 text-muted/50">·</span>
                  <span className="font-mono text-[10px] text-muted">
                    {p.type}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </SectionReveal>
      </div>
    </section>
  );
}
