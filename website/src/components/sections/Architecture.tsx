"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";
import { architectureNodes } from "@/lib/content";
import { SectionReveal } from "@/components/ui/SectionReveal";
import { cn } from "@/lib/cn";
import { useReducedMotion } from "@/hooks/useReducedMotion";

type Packet = {
  id: number;
  path: "in" | "out" | "internal";
  progress: number;
  label: string;
};

const LABELS_IN = ["message", "image", "voice", "ws event"];
const LABELS_OUT = ["TTS audio", "reply", "action", "memory write"];
const LABELS_INT = ["emotion Δ", "RAG hit", "tool call", "persona"];

export function Architecture() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { amount: 0.25 });
  const reduced = useReducedMotion();
  const [packets, setPackets] = useState<Packet[]>([]);
  const [activeNode, setActiveNode] = useState<string | null>("brain");
  const idRef = useRef(0);

  useEffect(() => {
    if (!inView || reduced) return;

    const spawn = () => {
      const roll = Math.random();
      const path: Packet["path"] =
        roll < 0.4 ? "in" : roll < 0.75 ? "internal" : "out";
      const labels =
        path === "in" ? LABELS_IN : path === "out" ? LABELS_OUT : LABELS_INT;
      const packet: Packet = {
        id: idRef.current++,
        path,
        progress: 0,
        label: labels[Math.floor(Math.random() * labels.length)],
      };
      setPackets((p) => [...p.slice(-14), packet]);

      // Pulse related nodes
      if (path === "in") setActiveNode(["discord", "telegram", "desktop"][Math.floor(Math.random() * 3)]);
      else if (path === "out") setActiveNode("voice");
      else
        setActiveNode(
          ["brain", "emotion", "memory", "persona"][Math.floor(Math.random() * 4)],
        );
    };

    spawn();
    const interval = setInterval(spawn, 900);
    return () => clearInterval(interval);
  }, [inView, reduced]);

  useEffect(() => {
    if (!inView || reduced) return;
    let raf = 0;
    let last = performance.now();
    const tick = (now: number) => {
      const dt = (now - last) / 1000;
      last = now;
      setPackets((prev) =>
        prev
          .map((p) => ({ ...p, progress: p.progress + dt * 0.38 }))
          .filter((p) => p.progress < 1.05),
      );
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, reduced]);

  return (
    <section
      id="architecture"
      className="section-y section-pad relative"
      ref={ref}
    >
      <div className="mx-auto max-w-6xl">
        <SectionReveal>
          <div className="mb-12 max-w-2xl">
            <p className="mb-3 text-xs font-medium tracking-[0.22em] text-lavender uppercase">
              Living architecture
            </p>
            <h2 className="text-display text-4xl text-ink sm:text-5xl md:text-[3.25rem]">
              Neural Hub at the center.
              <span className="block text-muted">Satellites in orbit.</span>
            </h2>
            <p className="text-body mt-5 max-w-xl text-base">
              Port 8000 orchestrates brain, emotion, memory, and persona.
              Discord, Telegram, and the Tauri desktop overlay stream in —
              plugins and senses stream out. Watch real data paths pulse
              through the system.
            </p>
          </div>
        </SectionReveal>

        <SectionReveal delay={0.12}>
          <div className="relative overflow-hidden rounded-3xl border border-glass-border bg-plum/60 p-4 sm:p-8 glow-lavender">
            <div className="grid-fade pointer-events-none absolute inset-0 opacity-60" />

            {/* SVG flow layer */}
            <div className="relative mx-auto aspect-[16/11] w-full max-w-5xl sm:aspect-[16/9]">
              <svg
                className="absolute inset-0 h-full w-full"
                viewBox="0 0 1000 560"
                fill="none"
                aria-hidden
              >
                {/* Hub ring */}
                <circle
                  cx="500"
                  cy="280"
                  r="118"
                  stroke="rgba(201,168,217,0.2)"
                  strokeWidth="1"
                />
                <circle
                  cx="500"
                  cy="280"
                  r="118"
                  stroke="rgba(201,168,217,0.35)"
                  strokeWidth="1"
                  strokeDasharray="4 8"
                  className={cn(!reduced && "flow-line")}
                />

                {/* Inbound paths from satellites */}
                <path
                  d="M120 100 C 220 120, 340 200, 420 240"
                  stroke="rgba(201,168,217,0.2)"
                  strokeWidth="1.5"
                  id="path-in-0"
                />
                <path
                  d="M120 280 C 240 280, 340 280, 382 280"
                  stroke="rgba(201,168,217,0.2)"
                  strokeWidth="1.5"
                  id="path-in-1"
                />
                <path
                  d="M120 460 C 220 430, 340 360, 420 320"
                  stroke="rgba(201,168,217,0.2)"
                  strokeWidth="1.5"
                  id="path-in-2"
                />

                {/* Outbound to senses */}
                <path
                  d="M580 220 C 680 160, 780 120, 880 100"
                  stroke="rgba(242,167,195,0.22)"
                  strokeWidth="1.5"
                  id="path-out-0"
                />
                <path
                  d="M618 280 C 720 280, 800 280, 880 280"
                  stroke="rgba(242,167,195,0.22)"
                  strokeWidth="1.5"
                  id="path-out-1"
                />
                <path
                  d="M580 340 C 680 400, 780 440, 880 460"
                  stroke="rgba(242,167,195,0.22)"
                  strokeWidth="1.5"
                  id="path-out-2"
                />

                {/* Internal cross links */}
                <path
                  d="M460 230 Q 500 200 540 230"
                  stroke="rgba(123,94,167,0.35)"
                  strokeWidth="1"
                  strokeDasharray="3 5"
                  className={cn(!reduced && "flow-line")}
                />
                <path
                  d="M460 330 Q 500 360 540 330"
                  stroke="rgba(123,94,167,0.35)"
                  strokeWidth="1"
                  strokeDasharray="3 5"
                  className={cn(!reduced && "flow-line")}
                />

                {/* Animated packets */}
                {!reduced &&
                  packets.map((p) => {
                    const pos = packetPosition(p);
                    return (
                      <g key={p.id}>
                        <circle
                          cx={pos.x}
                          cy={pos.y}
                          r="4"
                          fill={
                            p.path === "out"
                              ? "#F2A7C3"
                              : p.path === "in"
                                ? "#C9A8D9"
                                : "#7B5EA7"
                          }
                          opacity={0.9}
                        >
                          <animate
                            attributeName="r"
                            values="3;5;3"
                            dur="0.8s"
                            repeatCount="indefinite"
                          />
                        </circle>
                        <circle
                          cx={pos.x}
                          cy={pos.y}
                          r="10"
                          fill={
                            p.path === "out"
                              ? "#F2A7C333"
                              : p.path === "in"
                                ? "#C9A8D933"
                                : "#7B5EA733"
                          }
                        />
                      </g>
                    );
                  })}
              </svg>

              {/* Node cards overlaid */}
              <div className="pointer-events-none absolute inset-0">
                {/* Neural hub center */}
                <div className="absolute top-1/2 left-1/2 w-[min(42%,220px)] -translate-x-1/2 -translate-y-1/2">
                  <HubCard
                    title="Neural Hub"
                    subtitle="Port 8000"
                    nodes={architectureNodes.neural}
                    active={activeNode}
                    highlight
                  />
                </div>

                {/* Satellites left */}
                <div className="absolute top-[6%] left-0 w-[28%] space-y-2 sm:top-[8%] sm:space-y-3">
                  <ClusterLabel>Satellites</ClusterLabel>
                  {architectureNodes.satellites.map((n) => (
                    <NodePill
                      key={n.id}
                      label={n.label}
                      sub={n.sub}
                      active={activeNode === n.id}
                    />
                  ))}
                </div>

                {/* Senses right */}
                <div className="absolute top-[6%] right-0 w-[28%] space-y-2 text-right sm:top-[8%] sm:space-y-3">
                  <ClusterLabel className="text-right">Senses</ClusterLabel>
                  {architectureNodes.senses.map((n) => (
                    <NodePill
                      key={n.id}
                      label={n.label}
                      sub={n.sub}
                      active={activeNode === n.id}
                      align="right"
                    />
                  ))}
                </div>

                {/* Plugins bottom */}
                <div className="absolute bottom-0 left-1/2 flex w-[90%] -translate-x-1/2 flex-wrap items-center justify-center gap-2 sm:gap-3">
                  <ClusterLabel className="w-full text-center mb-1">
                    Plugin System · ElizaOS style
                  </ClusterLabel>
                  {architectureNodes.plugins.map((n) => (
                    <NodePill
                      key={n.id}
                      label={n.label}
                      sub={n.sub}
                      active={activeNode === n.id}
                      compact
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Live packet feed */}
            <div className="relative mt-6 flex flex-wrap items-center gap-3 border-t border-glass-border pt-4">
              <span className="flex items-center gap-2 text-[11px] tracking-wider text-lavender uppercase">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-bloom opacity-60" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-bloom" />
                </span>
                Live traffic
              </span>
              <div className="flex flex-1 flex-wrap gap-2">
                {packets.slice(-6).map((p) => (
                  <span
                    key={p.id}
                    className={cn(
                      "rounded-full px-2.5 py-0.5 text-[10px] font-mono",
                      p.path === "in" && "bg-lavender/15 text-lavender",
                      p.path === "out" && "bg-bloom/15 text-bloom",
                      p.path === "internal" && "bg-violet/20 text-mist",
                    )}
                  >
                    {p.label}
                  </span>
                ))}
                {packets.length === 0 && (
                  <span className="text-xs text-muted">Awaiting packets…</span>
                )}
              </div>
            </div>
          </div>
        </SectionReveal>
      </div>
    </section>
  );
}

function packetPosition(p: Packet) {
  const t = Math.min(p.progress, 1);
  if (p.path === "in") {
    // left → center
    const lane = p.id % 3;
    const y0 = [100, 280, 460][lane];
    const y1 = [240, 280, 320][lane];
    return {
      x: 120 + (420 - 120) * t,
      y: y0 + (y1 - y0) * t,
    };
  }
  if (p.path === "out") {
    const lane = p.id % 3;
    const y0 = [220, 280, 340][lane];
    const y1 = [100, 280, 460][lane];
    return {
      x: 580 + (880 - 580) * t,
      y: y0 + (y1 - y0) * t,
    };
  }
  // internal orbit around hub
  const angle = t * Math.PI * 2 + (p.id % 5) * 0.8;
  return {
    x: 500 + Math.cos(angle) * 90,
    y: 280 + Math.sin(angle) * 70,
  };
}

function HubCard({
  title,
  subtitle,
  nodes,
  active,
  highlight,
}: {
  title: string;
  subtitle: string;
  nodes: readonly { id: string; label: string; sub: string }[];
  active: string | null;
  highlight?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border p-3 sm:p-4 glass-strong",
        highlight && "border-lavender/30 shadow-[0_0_40px_-10px_rgba(201,168,217,0.45)]",
      )}
    >
      <div className="mb-2 text-center">
        <p className="text-[10px] tracking-[0.18em] text-lavender uppercase sm:text-[11px]">
          {subtitle}
        </p>
        <p className="text-display text-sm text-ink sm:text-base">{title}</p>
      </div>
      <div className="grid grid-cols-2 gap-1.5">
        {nodes.map((n) => (
          <div
            key={n.id}
            className={cn(
              "rounded-lg border px-1.5 py-1.5 text-center transition-all duration-500 sm:px-2",
              active === n.id
                ? "border-lavender/50 bg-lavender/15 text-mist"
                : "border-white/5 bg-void/40 text-muted",
            )}
          >
            <p className="text-[9px] font-medium sm:text-[10px]">{n.label}</p>
            <p className="hidden text-[8px] opacity-70 sm:block">{n.sub}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function NodePill({
  label,
  sub,
  active,
  align = "left",
  compact,
}: {
  label: string;
  sub: string;
  active?: boolean;
  align?: "left" | "right";
  compact?: boolean;
}) {
  return (
    <motion.div
      animate={{
        scale: active ? 1.04 : 1,
        borderColor: active
          ? "rgba(201,168,217,0.45)"
          : "rgba(201,168,217,0.12)",
      }}
      className={cn(
        "pointer-events-auto rounded-xl border bg-void/50 px-2.5 py-1.5 backdrop-blur-md sm:px-3 sm:py-2",
        compact && "inline-flex flex-col",
        align === "right" && "ml-auto",
        align === "left" && !compact && "mr-auto",
      )}
    >
      <p
        className={cn(
          "text-[11px] font-medium text-mist sm:text-xs",
          align === "right" && "text-right",
        )}
      >
        {label}
      </p>
      <p
        className={cn(
          "text-[9px] text-muted sm:text-[10px]",
          align === "right" && "text-right",
        )}
      >
        {sub}
      </p>
    </motion.div>
  );
}

function ClusterLabel({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <p
      className={cn(
        "text-[9px] tracking-[0.2em] text-lavender/70 uppercase sm:text-[10px]",
        className,
      )}
    >
      {children}
    </p>
  );
}
