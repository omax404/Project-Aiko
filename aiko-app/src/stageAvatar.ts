import { useEffect, useState } from 'react';

/**
 * Size and position of the Live2D model on the cinematic stage.
 * Stored in this app's local storage, so it applies instantly and needs no backend.
 */
export interface StageAvatar {
  scale: number; // 1 = normal size (0.4 - 2.2)
  x: number;     // horizontal shift in px, negative = left (-600 .. 600)
  y: number;     // vertical shift in px, negative = up (-600 .. 600)
}

export const DEFAULT_STAGE_AVATAR: StageAvatar = { scale: 1, x: 0, y: 0 };

export const STAGE_AVATAR_LIMITS = {
  scale: { min: 0.4, max: 2.2, step: 0.05 },
  x: { min: -600, max: 600, step: 10 },
  y: { min: -600, max: 600, step: 10 },
};

const KEY = 'aiko.stageAvatar.v1';
const EVENT = 'aiko-stage-avatar-change';

function clamp(v: unknown, min: number, max: number, fallback: number): number {
  const n = typeof v === 'number' && Number.isFinite(v) ? v : fallback;
  return Math.min(max, Math.max(min, n));
}

function normalize(raw: Partial<StageAvatar> | null | undefined): StageAvatar {
  const L = STAGE_AVATAR_LIMITS;
  return {
    scale: clamp(raw?.scale, L.scale.min, L.scale.max, DEFAULT_STAGE_AVATAR.scale),
    x: clamp(raw?.x, L.x.min, L.x.max, DEFAULT_STAGE_AVATAR.x),
    y: clamp(raw?.y, L.y.min, L.y.max, DEFAULT_STAGE_AVATAR.y),
  };
}

function load(): StageAvatar {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return normalize(JSON.parse(raw));
  } catch (_) {
    /* ignore corrupt / unavailable storage */
  }
  return { ...DEFAULT_STAGE_AVATAR };
}

let current: StageAvatar = load();

export function setStageAvatar(next: StageAvatar): void {
  current = normalize(next);
  window.dispatchEvent(new Event(EVENT));
  try {
    localStorage.setItem(KEY, JSON.stringify(current));
  } catch (_) {
    /* still applied for this session */
  }
}

export function useStageAvatar(): StageAvatar {
  const [value, setValue] = useState<StageAvatar>(current);
  useEffect(() => {
    const onChange = () => setValue({ ...current });
    window.addEventListener(EVENT, onChange);
    return () => window.removeEventListener(EVENT, onChange);
  }, []);
  return value;
}
