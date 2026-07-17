"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  emotions,
  type EmotionKey,
} from "@/lib/content";

type EmotionContextValue = {
  emotion: EmotionKey;
  setEmotion: (key: EmotionKey) => void;
  config: (typeof emotions)[EmotionKey];
  cycle: () => void;
};

const EmotionContext = createContext<EmotionContextValue | null>(null);

const ORDER: EmotionKey[] = [
  "calm",
  "joy",
  "focus",
  "alert",
  "melancholy",
  "affection",
];

export function EmotionProvider({ children }: { children: ReactNode }) {
  const [emotion, setEmotion] = useState<EmotionKey>("calm");

  const cycle = useCallback(() => {
    setEmotion((current) => {
      const i = ORDER.indexOf(current);
      return ORDER[(i + 1) % ORDER.length];
    });
  }, []);

  const value = useMemo(
    () => ({
      emotion,
      setEmotion,
      config: emotions[emotion],
      cycle,
    }),
    [emotion, cycle],
  );

  return (
    <EmotionContext.Provider value={value}>{children}</EmotionContext.Provider>
  );
}

export function useEmotion() {
  const ctx = useContext(EmotionContext);
  if (!ctx) throw new Error("useEmotion must be used within EmotionProvider");
  return ctx;
}
