/** Study mode: board geometry shared by the lesson player and its tests. */

export type LessonColor = 'ink' | 'red' | 'blue' | 'green' | 'gold' | 'purple';

export type DrawOp =
  | { type: 'text'; x: number; y: number; text: string; color: LessonColor }
  | { type: 'box'; x: number; y: number; w: number; h: number; text: string; color: LessonColor }
  | { type: 'circle'; x: number; y: number; r: number; text: string; color: LessonColor }
  | { type: 'arrow' | 'line'; x1: number; y1: number; x2: number; y2: number; color: LessonColor };

export interface LessonStep {
  narration: string;
  draw: DrawOp[];
}

export interface Lesson {
  title: string;
  slides?: string;
  steps: LessonStep[];
}

export const COLOR_HEX: Record<LessonColor, string> = {
  ink: '#f0ebe3',
  red: '#f87171',
  blue: '#60a5fa',
  green: '#4ade80',
  gold: '#e6c36a',
  purple: '#c4a1e8',
};

const clamp = (n: unknown, lo = 0, hi = 100): number => {
  const v = typeof n === 'number' && Number.isFinite(n) ? n : lo;
  return Math.max(lo, Math.min(hi, v));
};

/** Ops visible at a given step: everything drawn so far, in order. */
export function opsUpTo(steps: LessonStep[], stepIndex: number): { op: DrawOp; step: number }[] {
  const out: { op: DrawOp; step: number }[] = [];
  steps.slice(0, Math.max(0, stepIndex + 1)).forEach((s, step) => {
    (s.draw || []).forEach((op) => out.push({ op, step }));
  });
  return out;
}

/** Re-validate a lesson from the network before rendering (never trust the wire). */
export function normalizeLessons(data: unknown): Lesson[] {
  const list = (data as { lessons?: unknown })?.lessons;
  if (!Array.isArray(list)) return [];
  const lessons: Lesson[] = [];
  for (const raw of list) {
    const steps: LessonStep[] = [];
    for (const s of Array.isArray(raw?.steps) ? raw.steps : []) {
      if (typeof s?.narration !== 'string' || !s.narration.trim()) continue;
      const draw: DrawOp[] = [];
      for (const o of Array.isArray(s.draw) ? s.draw : []) {
        const color: LessonColor = o?.color in COLOR_HEX ? o.color : 'ink';
        if (o?.type === 'arrow' || o?.type === 'line') {
          draw.push({ type: o.type, x1: clamp(o.x1), y1: clamp(o.y1), x2: clamp(o.x2), y2: clamp(o.y2), color });
        } else if (o?.type === 'text' && typeof o.text === 'string') {
          draw.push({ type: 'text', x: clamp(o.x), y: clamp(o.y), text: o.text.slice(0, 90), color });
        } else if (o?.type === 'box') {
          draw.push({ type: 'box', x: clamp(o.x), y: clamp(o.y), w: clamp(o.w, 2), h: clamp(o.h, 2), text: String(o.text ?? '').slice(0, 90), color });
        } else if (o?.type === 'circle') {
          draw.push({ type: 'circle', x: clamp(o.x), y: clamp(o.y), r: clamp(o.r, 1, 50), text: String(o.text ?? '').slice(0, 90), color });
        }
      }
      steps.push({ narration: s.narration.slice(0, 600), draw });
    }
    if (steps.length) lessons.push({ title: String(raw?.title || 'Lesson').slice(0, 80), slides: raw?.slides, steps });
  }
  return lessons;
}
