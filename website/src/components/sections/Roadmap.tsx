"use client";

import { roadmap } from "@/lib/content";
import { SectionReveal } from "@/components/ui/SectionReveal";
import { GlassCard } from "@/components/ui/GlassCard";

export function Roadmap() {
  return (
    <section id="roadmap" className="section-y section-pad relative">
      <div className="mx-auto max-w-6xl">
        <SectionReveal>
          <div className="mb-12 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-xl">
              <p className="mb-3 text-xs font-medium tracking-[0.22em] text-lavender uppercase">
                Road to v1.0
              </p>
              <h2 className="text-display text-4xl text-ink sm:text-5xl">
                Still becoming.
              </h2>
              <p className="text-body mt-4 text-base">
                Open roadmap. Community-shaped. The systems already feel alive —
                these are the next layers of presence.
              </p>
            </div>
          </div>
        </SectionReveal>

        <div className="relative">
          {/* Timeline line */}
          <div
            className="absolute top-0 bottom-0 left-[15px] w-px bg-gradient-to-b from-lavender/50 via-violet/30 to-transparent sm:left-1/2 sm:-translate-x-px"
            aria-hidden
          />

          <ul className="space-y-6 sm:space-y-0">
            {roadmap.map((item, i) => {
              const left = i % 2 === 0;
              return (
                <SectionReveal key={item.title} delay={i * 0.06}>
                  <li className="relative sm:grid sm:grid-cols-2 sm:gap-10 sm:pb-10">
                    {/* Dot */}
                    <span
                      className="absolute top-5 left-[11px] z-10 h-2.5 w-2.5 rounded-full bg-lavender shadow-[0_0_12px_var(--lavender)] sm:left-1/2 sm:-translate-x-1/2"
                      aria-hidden
                    />

                    <div
                      className={
                        left
                          ? "pl-10 sm:col-start-1 sm:pr-6 sm:pl-0 sm:text-right"
                          : "pl-10 sm:col-start-2 sm:pl-6"
                      }
                    >
                      <GlassCard className="p-5 sm:p-6">
                        <div
                          className={`mb-2 flex items-center gap-2 ${left ? "sm:justify-end" : ""}`}
                        >
                          <span className="rounded-full border border-lavender/25 bg-lavender/10 px-2 py-0.5 text-[10px] tracking-wider text-lavender uppercase">
                            Upcoming
                          </span>
                        </div>
                        <h3 className="text-display text-xl text-ink">
                          {item.title}
                        </h3>
                        <p className="text-body mt-1.5 text-sm">
                          {item.description}
                        </p>
                      </GlassCard>
                    </div>

                    {/* Spacer for alternating layout */}
                    {left ? (
                      <div className="hidden sm:col-start-2 sm:block" />
                    ) : (
                      <div className="hidden sm:col-start-1 sm:row-start-1 sm:block" />
                    )}
                  </li>
                </SectionReveal>
              );
            })}
          </ul>
        </div>
      </div>
    </section>
  );
}
