import { describe, it, expect } from 'vitest';
import { normalizeLessons, opsUpTo } from '../lessonBoard';

describe('lessonBoard', () => {
  it('rejects malformed payloads', () => {
    expect(normalizeLessons(null)).toEqual([]);
    expect(normalizeLessons({ lessons: 'x' })).toEqual([]);
    expect(normalizeLessons({ lessons: [{ title: 'a', steps: [{ narration: '', draw: [] }] }] })).toEqual([]);
  });

  it('clamps coordinates, drops unknown ops, defaults colors', () => {
    const [lesson] = normalizeLessons({
      lessons: [{ title: 'T', steps: [{ narration: 'Hi', draw: [
        { type: 'box', x: 900, y: -4, w: 1, h: 30, text: 'a', color: 'neon' },
        { type: 'script', x: 1 },
        { type: 'arrow', x1: 1, y1: 2, x2: 3, y2: 4, color: 'red' },
      ] }] }],
    });
    expect(lesson?.steps[0]?.draw).toHaveLength(2);
    expect(lesson?.steps[0]?.draw[0]).toMatchObject({ x: 100, y: 0, w: 2, color: 'ink' });
  });

  it('accumulates drawings across steps', () => {
    const steps = [
      { narration: 'a', draw: [{ type: 'text', x: 1, y: 1, text: 'A', color: 'ink' } as const] },
      { narration: 'b', draw: [{ type: 'text', x: 2, y: 2, text: 'B', color: 'ink' } as const] },
    ];
    expect(opsUpTo(steps, 0)).toHaveLength(1);
    expect(opsUpTo(steps, 1).map((o) => o.step)).toEqual([0, 1]);
  });
});
