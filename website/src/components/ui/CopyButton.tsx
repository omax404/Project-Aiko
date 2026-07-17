"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/cn";

export function CopyButton({
  text,
  className,
  label = "Copy",
}: {
  text: string;
  className?: string;
  label?: string;
}) {
  const [copied, setCopied] = useState(false);

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* ignore */
    }
  };

  return (
    <button
      type="button"
      onClick={onCopy}
      className={cn(
        "btn-press relative inline-flex items-center gap-2 rounded-full border border-glass-border bg-midnight/60 px-3.5 py-1.5 text-xs font-medium text-lavender transition-all hover:border-lavender/40 hover:bg-lavender/10",
        className,
      )}
      data-cursor
      data-cursor-label={copied ? "Copied" : "Copy"}
      aria-label={copied ? "Copied to clipboard" : `Copy ${label}`}
    >
      <AnimatePresence mode="wait" initial={false}>
        {copied ? (
          <motion.span
            key="ok"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="flex items-center gap-1.5 text-bloom"
          >
            <CheckIcon />
            Copied
          </motion.span>
        ) : (
          <motion.span
            key="copy"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="flex items-center gap-1.5"
          >
            <CopyIcon />
            {label}
          </motion.span>
        )}
      </AnimatePresence>
    </button>
  );
}

function CopyIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect
        x="9"
        y="9"
        width="11"
        height="11"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.75"
      />
      <path
        d="M5 15V7a2 2 0 0 1 2-2h8"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M5 13l4 4L19 7"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
