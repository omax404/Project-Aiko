"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MagneticButton } from "@/components/ui/MagneticButton";
import { site } from "@/lib/content";
import { cn } from "@/lib/cn";

const links = [
  { href: "#positioning", label: "Why Aiko" },
  { href: "#architecture", label: "Architecture" },
  { href: "#capabilities", label: "Systems" },
  { href: "#quickstart", label: "Quick Start" },
  { href: "#roadmap", label: "Roadmap" },
];

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header
      className={cn(
        "fixed top-0 right-0 left-0 z-50 transition-all duration-500",
        scrolled
          ? "border-b border-glass-border bg-void/75 backdrop-blur-xl"
          : "bg-transparent",
      )}
    >
      <nav
        className="section-pad mx-auto flex h-16 max-w-6xl items-center justify-between sm:h-[4.25rem]"
        aria-label="Primary"
      >
        <a
          href="#top"
          className="group flex items-center gap-2.5"
          data-cursor
          data-cursor-label="Home"
        >
          <span className="relative flex h-8 w-8 items-center justify-center">
            <span className="absolute inset-0 rounded-full bg-lavender/20 animate-breathe" />
            <span className="relative h-2.5 w-2.5 rounded-full bg-lavender shadow-[0_0_12px_var(--lavender)]" />
          </span>
          <span className="text-display text-lg tracking-tight text-ink">
            Aiko
          </span>
        </a>

        <ul className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <li key={l.href}>
              <a
                href={l.href}
                className="rounded-full px-3.5 py-2 text-sm text-muted transition-colors hover:text-mist"
                data-cursor
              >
                {l.label}
              </a>
            </li>
          ))}
        </ul>

        <div className="hidden items-center gap-2 md:flex">
          <MagneticButton
            href={site.discord}
            variant="ghost"
            className="!px-4 !py-2 text-xs"
            strength={0.25}
          >
            Discord
          </MagneticButton>
          <MagneticButton
            href={site.github}
            variant="primary"
            className="!px-4 !py-2 text-xs"
            strength={0.25}
          >
            Star on GitHub
          </MagneticButton>
        </div>

        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-full border border-glass-border md:hidden"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          data-cursor
        >
          <span className="sr-only">Menu</span>
          <div className="flex w-4 flex-col gap-1.5">
            <span
              className={cn(
                "h-px w-full bg-mist transition-transform",
                open && "translate-y-[3.5px] rotate-45",
              )}
            />
            <span
              className={cn(
                "h-px w-full bg-mist transition-transform",
                open && "-translate-y-[3.5px] -rotate-45",
              )}
            />
          </div>
        </button>
      </nav>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="border-t border-glass-border bg-void/95 backdrop-blur-xl md:hidden"
          >
            <ul className="section-pad flex flex-col gap-1 py-4">
              {links.map((l) => (
                <li key={l.href}>
                  <a
                    href={l.href}
                    className="block rounded-xl px-3 py-3 text-base text-mist"
                    onClick={() => setOpen(false)}
                  >
                    {l.label}
                  </a>
                </li>
              ))}
              <li className="mt-2 flex flex-col gap-2 border-t border-glass-border pt-4">
                <a
                  href={site.discord}
                  className="rounded-full border border-glass-border px-4 py-3 text-center text-sm text-lavender"
                >
                  Join Discord
                </a>
                <a
                  href={site.github}
                  className="rounded-full bg-lavender px-4 py-3 text-center text-sm font-medium text-void"
                >
                  Star on GitHub
                </a>
              </li>
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
