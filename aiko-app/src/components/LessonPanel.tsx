import { useCallback, useEffect, useRef, useState } from 'react';
import { Pause, Play, SkipBack, SkipForward, Upload } from 'lucide-react';
import { getHubUrl, getAuthHeaders } from '../store/hubClient';
import { COLOR_HEX, DrawOp, Lesson, normalizeLessons, opsUpTo } from '../lessonBoard';

const FONT = 3.6;

function renderOp(op: DrawOp, key: string, fresh: boolean) {
  const stroke = COLOR_HEX[op.color];
  const cls = fresh ? 'lesson-draw' : undefined;
  const common = { stroke, strokeWidth: 0.5, fill: 'none', strokeLinecap: 'round' as const, className: cls };
  switch (op.type) {
    case 'text':
      return <text key={key} x={op.x} y={op.y} fill={stroke} fontSize={FONT} className={cls}>{op.text}</text>;
    case 'box':
      return (
        <g key={key} className={cls}>
          <rect x={op.x} y={op.y} width={op.w} height={op.h} rx={1.2} {...common} className={undefined} />
          <text x={op.x + op.w / 2} y={op.y + op.h / 2 + FONT / 3} fill={stroke} fontSize={FONT} textAnchor="middle">{op.text}</text>
        </g>
      );
    case 'circle':
      return (
        <g key={key} className={cls}>
          <circle cx={op.x} cy={op.y} r={op.r} {...common} className={undefined} />
          <text x={op.x} y={op.y + FONT / 3} fill={stroke} fontSize={FONT} textAnchor="middle">{op.text}</text>
        </g>
      );
    case 'arrow':
    case 'line': {
      const angle = Math.atan2(op.y2 - op.y1, op.x2 - op.x1);
      const head = 2.2;
      const hx = (a: number) => op.x2 - head * Math.cos(angle + a);
      const hy = (a: number) => op.y2 - head * Math.sin(angle + a);
      return (
        <g key={key} className={cls}>
          <line x1={op.x1} y1={op.y1} x2={op.x2} y2={op.y2} {...common} className={undefined} />
          {op.type === 'arrow' && (
            <path d={`M${hx(0.5)},${hy(0.5)} L${op.x2},${op.y2} L${hx(-0.5)},${hy(-0.5)}`} {...common} className={undefined} />
          )}
        </g>
      );
    }
  }
}

/** Settings > Memory: turn lecture slides into short lessons drawn live while Aiko talks. */
export function LessonPanel() {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [lessonIdx, setLessonIdx] = useState(0);
  const [stepIdx, setStepIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  const playToken = useRef(0);

  const lesson = lessons[lessonIdx];
  const step = lesson?.steps[stepIdx];
  const canSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window;

  const stop = useCallback(() => {
    playToken.current++;
    setPlaying(false);
    if (canSpeak) window.speechSynthesis.cancel();
  }, [canSpeak]);

  useEffect(() => stop, [stop]);

  // Narrate the current step; advance when speech ends (or after a reading delay).
  useEffect(() => {
    if (!playing || !step) return;
    const token = ++playToken.current;
    const next = () => {
      if (playToken.current !== token) return;
      if (stepIdx + 1 < lesson.steps.length) setStepIdx(stepIdx + 1);
      else setPlaying(false);
    };
    if (canSpeak) {
      const u = new SpeechSynthesisUtterance(step.narration);
      u.onend = next;
      u.onerror = next;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
      return () => { playToken.current++; window.speechSynthesis.cancel(); };
    }
    const t = window.setTimeout(next, Math.max(3000, step.narration.length * 60));
    return () => { playToken.current++; window.clearTimeout(t); };
  }, [playing, stepIdx, lessonIdx, lessons]); // eslint-disable-line react-hooks/exhaustive-deps

  const onFile = async (file: File | undefined) => {
    if (!file) return;
    stop();
    setBusy(true);
    setStatus('Mommy is reading your slides... this can take a minute.');
    try {
      const body = new FormData();
      body.append('file', file);
      const headers = await getAuthHeaders();
      const res = await fetch(`${getHubUrl()}/api/lessons`, { method: 'POST', headers, body });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
      const parsed = normalizeLessons(data);
      if (!parsed.length) throw new Error('No lessons came back');
      setLessons(parsed);
      setLessonIdx(0);
      setStepIdx(0);
      setStatus(`${parsed.length} lesson${parsed.length > 1 ? 's' : ''} ready.`);
    } catch (e: any) {
      setStatus(`Could not make lessons: ${e?.message || e}`);
    } finally {
      setBusy(false);
    }
  };

  const go = (delta: number) => {
    stop();
    setStepIdx((i) => Math.max(0, Math.min((lesson?.steps.length || 1) - 1, i + delta)));
  };

  const visible = lesson ? opsUpTo(lesson.steps, stepIdx) : [];

  return (
    <section className="p-4 rounded-xl bg-[var(--bg-base)] border border-white/[0.06]">
      <style>{`.lesson-draw{animation:lessonFade .6s ease both}@keyframes lessonFade{from{opacity:0}to{opacity:1}}@media (prefers-reduced-motion:reduce){.lesson-draw{animation:none}}`}</style>
      <span className="block text-[13px] font-medium text-[#f0ebe3]">Study with Aiko</span>
      <p className="text-[12px] text-[#9a8f7e] mt-1 mb-3">
        Upload lecture slides (PDF or PPTX). Aiko turns them into short lessons and draws each one on the board while she explains it.
      </p>
      <label className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-[var(--accent)]/15 text-[var(--accent)] text-[12px] cursor-pointer hover:bg-[var(--accent)]/25">
        <Upload size={14} /> {busy ? 'Working...' : 'Choose slides'}
        <input type="file" accept=".pdf,.pptx" className="sr-only" disabled={busy} onChange={(e) => { onFile(e.target.files?.[0]); e.target.value = ''; }} />
      </label>
      {status && <p role="status" className="text-[12px] text-[#9a8f7e] mt-2">{status}</p>}

      {lesson && step && (
        <div className="mt-4 flex flex-col gap-3">
          {lessons.length > 1 && (
            <select
              aria-label="Lesson"
              className="bg-[#181612] border border-white/[0.06] rounded-lg p-2 text-[12px] text-[#f0ebe3]"
              value={lessonIdx}
              onChange={(e) => { stop(); setLessonIdx(Number(e.target.value)); setStepIdx(0); }}
            >
              {lessons.map((l, i) => <option key={i} value={i}>{l.title}{l.slides ? ` (slides ${l.slides})` : ''}</option>)}
            </select>
          )}
          <svg viewBox="0 0 100 100" role="img" aria-label={`Whiteboard: ${lesson.title}`} className="w-full aspect-[4/3] rounded-xl bg-[#14110e] border border-white/[0.06]">
            {visible.map(({ op, step: s }, i) => renderOp(op, `${lessonIdx}-${i}`, s === stepIdx))}
          </svg>
          <p className="text-[13px] text-[#f0ebe3] leading-relaxed" aria-live="polite">{step.narration}</p>
          <div className="flex items-center gap-2">
            <button type="button" aria-label="Previous step" className="p-2 text-[#9a8f7e] hover:text-[#f0ebe3]" onClick={() => go(-1)}><SkipBack size={16} /></button>
            <button type="button" aria-label={playing ? 'Pause' : 'Play'} className="p-2 rounded-lg bg-[var(--accent)]/15 text-[var(--accent)]" onClick={() => (playing ? stop() : setPlaying(true))}>
              {playing ? <Pause size={16} /> : <Play size={16} />}
            </button>
            <button type="button" aria-label="Next step" className="p-2 text-[#9a8f7e] hover:text-[#f0ebe3]" onClick={() => go(1)}><SkipForward size={16} /></button>
            <span className="text-[11px] text-[#5a5248] ml-auto">Step {stepIdx + 1} / {lesson.steps.length}</span>
          </div>
        </div>
      )}
    </section>
  );
}
