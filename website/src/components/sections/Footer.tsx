"use client";

import { site } from "@/lib/content";
import { MagneticButton } from "@/components/ui/MagneticButton";

export function Footer() {
  return (
    <footer className="relative border-t border-glass-border">
      <div className="section-pad mx-auto max-w-6xl py-16 sm:py-20">
        <div className="grid gap-12 lg:grid-cols-[1.4fr_1fr]">
          <div>
            <div className="mb-4 flex items-center gap-2.5">
              <span className="relative flex h-8 w-8 items-center justify-center">
                <span className="absolute inset-0 rounded-full bg-lavender/20 animate-breathe" />
                <span className="relative h-2.5 w-2.5 rounded-full bg-lavender shadow-[0_0_12px_var(--lavender)]" />
              </span>
              <span className="text-display text-2xl text-ink">Aiko</span>
            </div>
            <p className="text-display max-w-md text-2xl leading-snug text-mist sm:text-3xl">
              &ldquo;{site.quote}&rdquo;
            </p>
            <p className="text-body mt-4 max-w-sm text-sm">
              Self-hosted emotional intelligence. Built by the Aiko Team.
              Licensed {site.license}.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <MagneticButton href={site.github} variant="primary">
                ⭐ Star this repo
              </MagneticButton>
              <MagneticButton href={site.discord} variant="ghost">
                Join Discord
              </MagneticButton>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-8 sm:grid-cols-3 lg:grid-cols-2">
            <div>
              <p className="mb-3 text-[11px] tracking-[0.18em] text-lavender uppercase">
                Product
              </p>
              <ul className="space-y-2 text-sm text-muted">
                <li>
                  <a href="#positioning" className="hover:text-mist">
                    Why Aiko
                  </a>
                </li>
                <li>
                  <a href="#architecture" className="hover:text-mist">
                    Architecture
                  </a>
                </li>
                <li>
                  <a href="#capabilities" className="hover:text-mist">
                    Systems
                  </a>
                </li>
                <li>
                  <a href="#quickstart" className="hover:text-mist">
                    Quick Start
                  </a>
                </li>
                <li>
                  <a href="#roadmap" className="hover:text-mist">
                    Roadmap
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <p className="mb-3 text-[11px] tracking-[0.18em] text-lavender uppercase">
                Community
              </p>
              <ul className="space-y-2 text-sm text-muted">
                <li>
                  <a
                    href={site.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-mist"
                  >
                    GitHub
                  </a>
                </li>
                <li>
                  <a
                    href={site.discord}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-mist"
                  >
                    Discord
                  </a>
                </li>
                <li>
                  <a
                    href={site.wiki}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-mist"
                  >
                    Wiki / Docs
                  </a>
                </li>
                <li>
                  <a
                    href={`${site.github}/blob/main/CONTRIBUTING.md`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-mist"
                  >
                    Contribute
                  </a>
                </li>
              </ul>
            </div>
            <div className="col-span-2 sm:col-span-1 lg:col-span-2">
              <p className="mb-3 text-[11px] tracking-[0.18em] text-lavender uppercase">
                Related
              </p>
              <ul className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-muted">
                <li>
                  <a
                    href="https://github.com/kyutai-labs/pocket-tts"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-mist"
                  >
                    Pocket-TTS
                  </a>
                </li>
                <li>
                  <a
                    href="https://github.com/MemPalace/mempalace"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-mist"
                  >
                    MemPalace
                  </a>
                </li>
                <li>
                  <a
                    href="https://github.com/ollama/ollama"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-mist"
                  >
                    Ollama
                  </a>
                </li>
                <li>
                  <a
                    href="https://github.com/guansss/pixi-live2d-display"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-mist"
                  >
                    Live2D Display
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-14 flex flex-col items-start justify-between gap-3 border-t border-glass-border pt-8 sm:flex-row sm:items-center">
          <p className="text-xs text-muted">
            © {new Date().getFullYear()} Aiko Team · {site.license} License
          </p>
          <p className="text-xs text-muted">
            Built with care for people who want their AI{" "}
            <span className="text-lavender">close</span>, not clouded.
          </p>
        </div>
      </div>
    </footer>
  );
}
