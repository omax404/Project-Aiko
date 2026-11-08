import { useRef } from 'react';
import type { ReactNode, PointerEvent, MouseEvent, WheelEvent } from 'react';
import { setStageAvatar, STAGE_AVATAR_LIMITS, useStageAvatar } from '../stageAvatar';

/**
 * Wraps Aiko's model on the stage: drag to move her, Ctrl + mouse wheel to resize.
 * A plain click (no movement) still reaches the model, so touching her keeps working.
 * Size and position are shared with Settings > Appearance.
 */
export function DraggableAvatar({ children }: { children: ReactNode }) {
  const avatar = useStageAvatar();
  const drag = useRef<{ sx: number; sy: number; ox: number; oy: number; moved: boolean } | null>(null);
  const suppressClick = useRef(false);

  const onPointerDown = (e: PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0) return;
    drag.current = { sx: e.clientX, sy: e.clientY, ox: avatar.x, oy: avatar.y, moved: false };
  };

  const onPointerMove = (e: PointerEvent<HTMLDivElement>) => {
    const d = drag.current;
    if (!d) return;
    const dx = e.clientX - d.sx;
    const dy = e.clientY - d.sy;
    if (!d.moved) {
      if (Math.hypot(dx, dy) < 5) return;
      d.moved = true;
      try {
        e.currentTarget.setPointerCapture(e.pointerId);
      } catch {
        /* capture is optional */
      }
    }
    setStageAvatar({ ...avatar, x: d.ox + dx, y: d.oy + dy });
  };

  const endDrag = (e: PointerEvent<HTMLDivElement>) => {
    const d = drag.current;
    drag.current = null;
    if (d?.moved) {
      suppressClick.current = true;
      setTimeout(() => {
        suppressClick.current = false;
      }, 0);
      try {
        e.currentTarget.releasePointerCapture(e.pointerId);
      } catch {
        /* already released */
      }
    }
  };

  // After a drag, swallow the click so she does not react as if she were touched.
  const onClickCapture = (e: MouseEvent<HTMLDivElement>) => {
    if (suppressClick.current) {
      e.stopPropagation();
      e.preventDefault();
    }
  };

  const onWheel = (e: WheelEvent<HTMLDivElement>) => {
    if (!e.ctrlKey) return;
    const { min, max } = STAGE_AVATAR_LIMITS.scale;
    const next = Math.min(max, Math.max(min, avatar.scale * (e.deltaY < 0 ? 1.06 : 1 / 1.06)));
    setStageAvatar({ ...avatar, scale: Math.round(next * 100) / 100 });
  };

  return (
    <div
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      onClickCapture={onClickCapture}
      onWheel={onWheel}
      title="Drag to move her. Ctrl + wheel to resize."
      style={{
        transform: `translate(${avatar.x}px, ${avatar.y}px) scale(${avatar.scale})`,
        transformOrigin: 'center center',
        willChange: 'transform',
        touchAction: 'none',
        cursor: drag.current?.moved ? 'grabbing' : 'grab',
      }}
    >
      {children}
    </div>
  );
}
