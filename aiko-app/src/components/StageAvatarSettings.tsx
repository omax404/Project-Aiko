import React from 'react';
import { RotateCcw } from 'lucide-react';
import {
  DEFAULT_STAGE_AVATAR,
  STAGE_AVATAR_LIMITS,
  StageAvatar,
  setStageAvatar,
  useStageAvatar,
} from '../stageAvatar';

/** Appearance-tab section: change the size and position of Aiko's 2D model. Changes apply live. */
export const StageAvatarSettings: React.FC = () => {
  const avatar = useStageAvatar();
  const L = STAGE_AVATAR_LIMITS;

  const update = (patch: Partial<StageAvatar>) => setStageAvatar({ ...avatar, ...patch });

  const slider = (
    label: string,
    value: number,
    display: string,
    limits: { min: number; max: number; step: number },
    onChange: (v: number) => void,
  ) => (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-[11px] text-[#9a8f7e]">
        <span>{label}</span>
        <span className="font-mono text-[var(--accent)]">{display}</span>
      </div>
      <input
        type="range"
        min={limits.min}
        max={limits.max}
        step={limits.step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full accent-[var(--accent)]"
        aria-label={label}
      />
    </div>
  );

  return (
    <div className="flex flex-col gap-3 p-3 rounded-lg bg-[var(--bg-base)] border border-white/[0.06]">
      <div className="flex items-center justify-between">
        <label className="text-[12px] font-medium text-[#9a8f7e]">2D Model Size & Position</label>
        <button
          type="button"
          onClick={() => setStageAvatar({ ...DEFAULT_STAGE_AVATAR })}
          className="flex items-center gap-1 text-[11px] text-[#9a8f7e] hover:text-[var(--accent)]"
          title="Reset size and position"
        >
          <RotateCcw size={12} /> Reset
        </button>
      </div>

      {slider('Size', avatar.scale, `${Math.round(avatar.scale * 100)}%`, L.scale, (v) => update({ scale: v }))}
      {slider(
        'Horizontal (left / right)',
        avatar.x,
        avatar.x === 0 ? 'center' : `${avatar.x > 0 ? '→' : '←'} ${Math.abs(avatar.x)}px`,
        L.x,
        (v) => update({ x: v }),
      )}
      {slider(
        'Vertical (up / down)',
        avatar.y,
        avatar.y === 0 ? 'center' : `${avatar.y > 0 ? '↓' : '↑'} ${Math.abs(avatar.y)}px`,
        L.y,
        (v) => update({ y: v }),
      )}

      <span className="text-[10px] text-[#5a5248] uppercase tracking-tight">
        Applies instantly and is remembered. Use Reset to put her back in the middle.
      </span>
    </div>
  );
};
