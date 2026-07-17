"use client";

import { useRef, type ReactNode, type MouseEvent } from "react";
import { motion, useMotionTemplate, useMotionValue, useSpring } from "framer-motion";
import { cn } from "@/lib/cn";
import { useReducedMotion } from "@/hooks/useReducedMotion";

type Props = {
  children: ReactNode;
  className?: string;
  glow?: boolean;
};

export function GlassCard({ children, className, glow = true }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion();
  const mx = useMotionValue(50);
  const my = useMotionValue(50);
  const rx = useSpring(0, { stiffness: 180, damping: 20 });
  const ry = useSpring(0, { stiffness: 180, damping: 20 });

  const background = useMotionTemplate`radial-gradient(420px circle at ${mx}% ${my}%, rgba(201,168,217,0.14), transparent 55%)`;

  const onMove = (e: MouseEvent) => {
    if (!ref.current || reduced) return;
    const rect = ref.current.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * 100;
    const py = ((e.clientY - rect.top) / rect.height) * 100;
    mx.set(px);
    my.set(py);
    const nx = (e.clientX - rect.left) / rect.width - 0.5;
    const ny = (e.clientY - rect.top) / rect.height - 0.5;
    ry.set(nx * 8);
    rx.set(-ny * 8);
  };

  const onLeave = () => {
    rx.set(0);
    ry.set(0);
    mx.set(50);
    my.set(50);
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      style={{
        rotateX: rx,
        rotateY: ry,
        transformStyle: "preserve-3d",
        perspective: 1000,
      }}
      className={cn(
        "group relative rounded-2xl glass overflow-hidden transition-shadow duration-500",
        glow && "hover:glow-lavender",
        className,
      )}
    >
      <motion.div
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100"
        style={{ background }}
        aria-hidden
      />
      <div className="relative z-10" style={{ transform: "translateZ(20px)" }}>
        {children}
      </div>
    </motion.div>
  );
}
