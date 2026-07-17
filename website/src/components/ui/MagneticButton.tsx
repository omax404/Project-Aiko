"use client";

import { useRef, type ReactNode, type MouseEvent } from "react";
import { motion, useMotionValue, useSpring } from "framer-motion";
import { cn } from "@/lib/cn";
import { useReducedMotion } from "@/hooks/useReducedMotion";

type Props = {
  children: ReactNode;
  className?: string;
  href?: string;
  strength?: number;
  variant?: "primary" | "ghost" | "soft";
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
  "aria-label"?: string;
};

export function MagneticButton({
  children,
  className,
  href,
  strength = 0.35,
  variant = "primary",
  onClick,
  type = "button",
  "aria-label": ariaLabel,
}: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion();
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const x = useSpring(mx, { stiffness: 220, damping: 18, mass: 0.4 });
  const y = useSpring(my, { stiffness: 220, damping: 18, mass: 0.4 });

  const onMove = (e: MouseEvent) => {
    if (reduced || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const dx = e.clientX - (rect.left + rect.width / 2);
    const dy = e.clientY - (rect.top + rect.height / 2);
    mx.set(dx * strength);
    my.set(dy * strength);
  };

  const onLeave = () => {
    mx.set(0);
    my.set(0);
  };

  const variants = {
    primary:
      "bg-lavender text-void hover:bg-mist shadow-[0_0_0_1px_rgba(201,168,217,0.3),0_8px_32px_-8px_rgba(201,168,217,0.45)]",
    ghost:
      "bg-transparent text-mist border border-glass-border hover:border-lavender/40 hover:bg-lavender/5",
    soft: "bg-midnight/80 text-lavender border border-glass-border hover:border-lavender/35 glass",
  };

  const base =
    "btn-press relative inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-sm font-medium tracking-wide transition-colors duration-300 will-change-transform";

  const classes = cn(base, variants[variant], className);

  return (
    <motion.div
      ref={ref}
      style={{ x, y }}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      className="inline-flex"
    >
      {href ? (
        <a
          href={href}
          className={classes}
          data-cursor
          data-cursor-label="Open"
          aria-label={ariaLabel}
        >
          {children}
        </a>
      ) : (
        <button
          type={type}
          onClick={onClick}
          className={classes}
          data-cursor
          aria-label={ariaLabel}
        >
          {children}
        </button>
      )}
    </motion.div>
  );
}
