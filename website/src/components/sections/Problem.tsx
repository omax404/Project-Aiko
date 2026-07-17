"use client";

import { comparison } from "@/lib/content";
import { SectionReveal } from "@/components/ui/SectionReveal";
import { GlassCard } from "@/components/ui/GlassCard";
import { cn } from "@/lib/cn";

export function Problem() {
  return (
    <section id="positioning" className="section-y section-pad relative">
      <div className="mx-auto max-w-6xl">
        <div className="mb-14 max-w-3xl" data-reveal>
          <p className="mb-3 text-xs font-medium tracking-[0.22em] text-lavender uppercase">
            Why Aiko ≠ other companions
          </p>
          <h2 className="text-display text-4xl text-ink sm:text-5xl md:text-[3.25rem]">
            Not a chatbot wrapper.
            <span className="mt-2 block text-muted">
              A living neural ecosystem.
            </span>
          </h2>
          <p className="text-body mt-5 max-w-2xl text-base sm:text-lg">
            Most companions are a personality prompt on a chat buffer. Aiko
            runs neuromodulators, unified memory, local voice, multimodal
            vision, and a proactive ReAct agent with real tools — on your
            machine, under your control.
          </p>
        </div>

        {/* Comparison table — desktop */}
        <SectionReveal delay={0.1}>
          <div className="hidden overflow-hidden rounded-2xl border border-glass-border md:block">
            <div className="grid grid-cols-[1.1fr_1.4fr_1.8fr] border-b border-glass-border bg-midnight/60 text-[11px] tracking-[0.16em] text-muted uppercase">
              <div className="px-5 py-3.5">Capability</div>
              <div className="border-l border-glass-border px-5 py-3.5">
                Most AI companions
              </div>
              <div className="border-l border-glass-border px-5 py-3.5 text-lavender">
                Aiko
              </div>
            </div>
            {comparison.map((row, i) => (
              <div
                key={row.capability}
                className={cn(
                  "grid grid-cols-[1.1fr_1.4fr_1.8fr] border-b border-glass-border last:border-b-0 transition-colors hover:bg-lavender/[0.03]",
                  i % 2 === 1 && "bg-plum/30",
                )}
              >
                <div className="px-5 py-4 text-sm font-medium text-mist">
                  {row.capability}
                </div>
                <div className="border-l border-glass-border px-5 py-4 text-sm text-muted">
                  {row.others}
                </div>
                <div className="border-l border-glass-border bg-lavender/[0.04] px-5 py-4 text-sm text-mist">
                  {row.aiko}
                </div>
              </div>
            ))}
          </div>
        </SectionReveal>

        {/* Mobile cards */}
        <div className="grid gap-3 md:hidden">
          {comparison.map((row, i) => (
            <SectionReveal key={row.capability} delay={i * 0.04}>
              <GlassCard className="p-4">
                <p className="mb-3 text-xs font-medium tracking-wider text-lavender uppercase">
                  {row.capability}
                </p>
                <div className="space-y-2">
                  <div>
                    <p className="text-[10px] tracking-wide text-muted uppercase">
                      Others
                    </p>
                    <p className="text-sm text-muted">{row.others}</p>
                  </div>
                  <div className="rounded-lg border border-lavender/20 bg-lavender/5 p-2.5">
                    <p className="text-[10px] tracking-wide text-lavender uppercase">
                      Aiko
                    </p>
                    <p className="text-sm text-mist">{row.aiko}</p>
                  </div>
                </div>
              </GlassCard>
            </SectionReveal>
          ))}
        </div>

        {/* Positioning pillars */}
        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          {[
            {
              title: "Self-hosted",
              body: "Your machine. Your keys. Your data. No rent-seeking cloud companion.",
            },
            {
              title: "Emotionally real",
              body: "Four neuromodulators, 22+ states, identity attractors — mood that actually moves.",
            },
            {
              title: "Agentic",
              body: "She decides when to speak, what to observe, and what tools to run.",
            },
          ].map((item, i) => (
            <SectionReveal key={item.title} delay={0.15 + i * 0.08}>
              <GlassCard className="h-full p-6">
                <div className="mb-4 h-px w-10 bg-gradient-to-r from-lavender to-transparent" />
                <h3 className="text-display text-xl text-ink">{item.title}</h3>
                <p className="text-body mt-2 text-sm">{item.body}</p>
              </GlassCard>
            </SectionReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
