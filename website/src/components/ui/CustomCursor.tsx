"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useSpring } from "framer-motion";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { useEmotion } from "@/components/providers/EmotionProvider";

export function CustomCursor() {
  const reduced = useReducedMotion();
  const { config } = useEmotion();
  const [visible, setVisible] = useState(false);
  const [hovering, setHovering] = useState(false);
  const [clicking, setClicking] = useState(false);
  const [label, setLabel] = useState("");
  const enabled = useRef(false);

  const x = useSpring(0, { stiffness: 450, damping: 38, mass: 0.35 });
  const y = useSpring(0, { stiffness: 450, damping: 38, mass: 0.35 });
  const ringX = useSpring(0, { stiffness: 180, damping: 24, mass: 0.5 });
  const ringY = useSpring(0, { stiffness: 180, damping: 24, mass: 0.5 });

  useEffect(() => {
    const fine = window.matchMedia("(pointer: fine)").matches;
    if (!fine || reduced) return;
    enabled.current = true;
    document.body.classList.add("has-custom-cursor");

    const onMove = (e: MouseEvent) => {
      x.set(e.clientX);
      y.set(e.clientY);
      ringX.set(e.clientX);
      ringY.set(e.clientY);
      setVisible(true);
    };

    const onOver = (e: MouseEvent) => {
      const t = (e.target as HTMLElement)?.closest?.(
        "a, button, [data-cursor], input, textarea, select, [role='button']",
      ) as HTMLElement | null;
      if (t) {
        setHovering(true);
        setLabel(t.dataset.cursorLabel ?? "");
      } else {
        setHovering(false);
        setLabel("");
      }
    };

    const onDown = () => setClicking(true);
    const onUp = () => setClicking(false);
    const onLeave = () => setVisible(false);

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseover", onOver);
    window.addEventListener("mousedown", onDown);
    window.addEventListener("mouseup", onUp);
    document.addEventListener("mouseleave", onLeave);

    return () => {
      document.body.classList.remove("has-custom-cursor");
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseover", onOver);
      window.removeEventListener("mousedown", onDown);
      window.removeEventListener("mouseup", onUp);
      document.removeEventListener("mouseleave", onLeave);
    };
  }, [reduced, x, y, ringX, ringY]);

  if (reduced) return null;

  return (
    <div
      className="pointer-events-none fixed inset-0 z-[9999] hidden md:block"
      aria-hidden
    >
      <motion.div
        className="absolute top-0 left-0 rounded-full mix-blend-difference"
        style={{
          x,
          y,
          width: hovering ? 12 : 6,
          height: hovering ? 12 : 6,
          marginLeft: hovering ? -6 : -3,
          marginTop: hovering ? -6 : -3,
          background: config.color,
          scale: clicking ? 0.7 : 1,
          opacity: visible ? 1 : 0,
        }}
      />
      <motion.div
        className="absolute top-0 left-0 rounded-full border"
        style={{
          x: ringX,
          y: ringY,
          width: hovering ? 52 : 32,
          height: hovering ? 52 : 32,
          marginLeft: hovering ? -26 : -16,
          marginTop: hovering ? -26 : -16,
          borderColor: config.color,
          opacity: visible ? (hovering ? 0.55 : 0.3) : 0,
          scale: clicking ? 0.85 : 1,
          boxShadow: hovering
            ? `0 0 24px ${config.color}55`
            : `0 0 12px ${config.color}22`,
        }}
      />
      {label && hovering && (
        <motion.div
          className="absolute top-0 left-0 whitespace-nowrap rounded-full px-2.5 py-1 text-[10px] font-medium tracking-wide uppercase"
          style={{
            x: ringX,
            y: ringY,
            marginTop: 28,
            marginLeft: -20,
            background: "rgba(28,19,32,0.9)",
            color: config.secondary,
            border: `1px solid ${config.color}44`,
            opacity: visible ? 1 : 0,
          }}
        >
          {label}
        </motion.div>
      )}
    </div>
  );
}
