"use client";

import { useState } from "react";
import {
  quickStartDev,
  quickStartDesktop,
  quickStartUser,
  site,
} from "@/lib/content";
import { SectionReveal } from "@/components/ui/SectionReveal";
import { CopyButton } from "@/components/ui/CopyButton";
import { MagneticButton } from "@/components/ui/MagneticButton";
import { cn } from "@/lib/cn";

type Tab = "user" | "dev" | "desktop";

export function QuickStart() {
  const [tab, setTab] = useState<Tab>("user");

  return (
    <section id="quickstart" className="section-y section-pad relative">
      <div className="mx-auto max-w-6xl">
        <SectionReveal>
          <div className="mb-12 max-w-2xl">
            <p className="mb-3 text-xs font-medium tracking-[0.22em] text-lavender uppercase">
              Quick start
            </p>
            <h2 className="text-display text-4xl text-ink sm:text-5xl">
              From zero to{" "}
              <span className="text-lavender">awake</span>
              <span className="text-muted">.</span>
            </h2>
            <p className="text-body mt-4 text-base">
              Windows users: double-click and wait. Developers: four commands
              and the Neural Hub is live on port 8000.
            </p>
          </div>
        </SectionReveal>

        <SectionReveal delay={0.1}>
          <div className="overflow-hidden rounded-3xl border border-glass-border glow-lavender">
            {/* Tab bar */}
            <div className="flex flex-wrap items-center gap-1 border-b border-glass-border bg-midnight/70 p-2 sm:p-3">
              {(
                [
                  { id: "user" as const, label: "Windows · no setup" },
                  { id: "dev" as const, label: "Developers" },
                  { id: "desktop" as const, label: "Desktop UI" },
                ] as const
              ).map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTab(t.id)}
                  className={cn(
                    "rounded-full px-4 py-2 text-xs font-medium transition-all sm:text-sm",
                    tab === t.id
                      ? "bg-lavender text-void"
                      : "text-muted hover:bg-white/5 hover:text-mist",
                  )}
                  data-cursor
                >
                  {t.label}
                </button>
              ))}
            </div>

            <div className="bg-void/80 p-5 sm:p-8">
              {tab === "user" && (
                <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
                  <ol className="space-y-4">
                    {quickStartUser.map((step, i) => (
                      <li key={step} className="flex gap-4">
                        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-lavender/30 bg-lavender/10 font-mono text-xs text-lavender">
                          {i + 1}
                        </span>
                        <p className="pt-1.5 text-sm text-mist sm:text-base">
                          {step}
                        </p>
                      </li>
                    ))}
                  </ol>
                  <div className="rounded-2xl border border-glass-border bg-plum/50 p-5">
                    <p className="mb-3 text-xs tracking-[0.16em] text-lavender uppercase">
                      Then customize
                    </p>
                    <ul className="space-y-2.5 text-sm text-muted">
                      <li>
                        <strong className="text-mist">Persona</strong> — custom
                        personality instructions
                      </li>
                      <li>
                        <strong className="text-mist">AI Model</strong> —
                        Ollama, Gemini, OpenAI, Anthropic, custom
                      </li>
                      <li>
                        <strong className="text-mist">Voice</strong> — enable
                        speech or change voice profile
                      </li>
                      <li>
                        <strong className="text-mist">Plugins</strong> —
                        Discord, Telegram, PC Bridge
                      </li>
                    </ul>
                    <p className="mt-4 text-xs text-muted">
                      Hit <span className="text-lavender">Save & Apply</span> —
                      changes take effect instantly.
                    </p>
                    <div className="mt-5">
                      <MagneticButton
                        href={site.github}
                        variant="primary"
                        className="w-full sm:w-auto"
                      >
                        Get Aiko on GitHub
                      </MagneticButton>
                    </div>
                  </div>
                </div>
              )}

              {tab === "dev" && (
                <div>
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <p className="text-xs text-muted">
                      Clones the repo, installs deps, launches Ollama + Neural
                      Hub + satellites + desktop overlay.
                    </p>
                    <CopyButton text={quickStartDev} label="Copy all" />
                  </div>
                  <pre className="code-block overflow-x-auto rounded-2xl border border-glass-border bg-plum/60 p-5 text-mist">
                    {quickStartDev.split("\n").map((line, i) => (
                      <div key={i} className="flex gap-4">
                        <span className="select-none text-muted/40">
                          {i + 1}
                        </span>
                        <code>
                          {line.startsWith("git") ||
                          line.startsWith("cd") ||
                          line.startsWith("pip") ||
                          line.startsWith("python") ? (
                            <>
                              <span className="text-bloom">
                                {line.split(" ")[0]}
                              </span>
                              <span> {line.split(" ").slice(1).join(" ")}</span>
                            </>
                          ) : (
                            line
                          )}
                        </code>
                      </div>
                    ))}
                  </pre>
                  <p className="mt-4 text-xs text-muted">
                    Optional voice cloning: accept terms on Hugging Face for{" "}
                    <code className="text-lavender">kyutai/pocket-tts</code>,
                    then{" "}
                    <code className="text-lavender">
                      huggingface-cli login
                    </code>
                    .
                  </p>
                </div>
              )}

              {tab === "desktop" && (
                <div>
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <p className="text-xs text-muted">
                      Modify the Tauri + React Live2D overlay.
                    </p>
                    <CopyButton text={quickStartDesktop} label="Copy all" />
                  </div>
                  <pre className="code-block overflow-x-auto rounded-2xl border border-glass-border bg-plum/60 p-5 text-mist">
                    {quickStartDesktop.split("\n").map((line, i) => (
                      <div key={i} className="flex gap-4">
                        <span className="select-none text-muted/40">
                          {i + 1}
                        </span>
                        <code>
                          {line.includes("#") ? (
                            <>
                              <span>{line.split("#")[0]}</span>
                              <span className="text-muted">
                                #{line.split("#")[1]}
                              </span>
                            </>
                          ) : (
                            line
                          )}
                        </code>
                      </div>
                    ))}
                  </pre>
                  <p className="mt-4 text-xs text-muted">
                    Production:{" "}
                    <code className="text-lavender">npm run tauri build</code>
                  </p>
                </div>
              )}
            </div>
          </div>
        </SectionReveal>
      </div>
    </section>
  );
}
