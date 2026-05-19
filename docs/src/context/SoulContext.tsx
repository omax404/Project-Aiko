import React, { createContext, useContext, useState, useCallback } from 'react';
import type { SoulMode } from '@/types/soul';
import { SOUL_MODES } from '@/types/soul';

interface SoulContextType {
  activeMode: SoulMode;
  setMode: (mode: SoulMode) => void;
  config: typeof SOUL_MODES[SoulMode];
}

const SoulContext = createContext<SoulContextType>({
  activeMode: 'devoted',
  setMode: () => {},
  config: SOUL_MODES.devoted,
});

export function SoulProvider({ children }: { children: React.ReactNode }) {
  const [activeMode, setActiveMode] = useState<SoulMode>('devoted');

  const setMode = useCallback((mode: SoulMode) => {
    setActiveMode(mode);
    // Update CSS custom properties for global theming
    const config = SOUL_MODES[mode];
    document.documentElement.style.setProperty('--accent-color', config.color);
    document.documentElement.style.setProperty('--glow-color', config.glowColor);
    document.documentElement.style.setProperty('--bg-tint', config.bgTint);
  }, []);

  return (
    <SoulContext.Provider value={{ activeMode, setMode, config: SOUL_MODES[activeMode] }}>
      {children}
    </SoulContext.Provider>
  );
}

export function useSoul() {
  return useContext(SoulContext);
}
