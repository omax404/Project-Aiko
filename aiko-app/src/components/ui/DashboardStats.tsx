import { Window, getCurrentWindow } from '@tauri-apps/api/window';
import { ChevronDown, ExternalLink, Heart, SlidersHorizontal } from 'lucide-react';
import { Live2DAvatar } from '../Live2DAvatar';
import { NeuralControlPanel } from '../NeuralControlPanel';
import { useNeuralStore } from '../../store/useNeuralStore';

interface DashboardStatsProps {
  bridgeStatus: any;
  isThinking: boolean;
  isTalking: boolean;
  currentEmotion: string;
  avatarScale: number;
  setAvatarScale: (s: number) => void;
  amplitude?: number;
  chemicals: any;
  isCompact?: boolean;
}

export function DashboardStats({
  bridgeStatus, isThinking, isTalking, currentEmotion,
  avatarScale, setAvatarScale, amplitude: propAmplitude, chemicals, isCompact
}: DashboardStatsProps) {
  const apiConfig = useNeuralStore(state => state.apiConfig);
  const storeAmplitude = useNeuralStore(state => state.amplitude);
  const amplitude = propAmplitude !== undefined ? propAmplitude : storeAmplitude;
  const connected = bridgeStatus?.status === 'connected';
  const width = isCompact ? 160 : 272;
  const emotionLabel = currentEmotion
    ? currentEmotion.replace(/[_-]+/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
    : 'Present';

  return (
    <aside
      aria-label="Aiko companion"
      className="flex h-full shrink-0 flex-col overflow-hidden border-l border-[var(--b1)] bg-[var(--bg-base)] transition-[width] duration-300"
      style={{ width: `${width}px`, minWidth: `${width}px` }}
    >
      {/* Avatar well: radial accent bloom on deep bg */}
      <div className="relative flex min-h-0 flex-1 items-center justify-center overflow-hidden"
        style={{ background: 'radial-gradient(ellipse at 50% 55%, color-mix(in oklab, var(--p-accent) 10%, transparent) 0%, transparent 68%)' }}
      >
        <Live2DAvatar
          modelUrl="/live2d/vivian/vivian.model3.json"
          isThinking={isThinking}
          isTalking={isTalking}
          emotion={currentEmotion}
          width={width}
          height={isCompact ? 300 : 480}
          scale={isCompact ? avatarScale * 0.65 : Math.min(avatarScale, 1.15)}
          amplitude={amplitude}
          chemicals={chemicals}
          interactive
        />

        {/* Status badge — taste-skill: ink dot, never off-palette green */}
        <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full border border-[var(--b1)] bg-[var(--bg-base)]/80 px-2.5 py-1.5 backdrop-blur-sm">
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ background: connected ? 'var(--p-accent)' : 'var(--t4)', opacity: connected ? 0.9 : 0.5 }}
          />
          <span className="text-[10px] font-medium text-[var(--t3)]">
            {connected ? 'Ready' : 'Waiting'}
          </span>
        </div>
      </div>

      {!isCompact && (
        <div className="shrink-0 border-t border-[var(--b1)] p-4 space-y-3">
          {/* Identity row */}
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-[var(--t1)] tracking-tight">Aiko</p>
              <p className="mt-0.5 truncate text-[11px] text-[var(--t3)]">
                {isThinking ? 'Thinking…' : isTalking ? 'Speaking' : emotionLabel}
              </p>
            </div>
            <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${
              connected
                ? 'bg-[var(--p-accent-soft)] text-[var(--p-accent)]'
                : 'bg-[var(--bg-hover)] text-[var(--t4)]'
            }`}>
              {connected ? 'Online' : 'Offline'}
            </span>
          </div>

          {/* Desktop companion CTA */}
          <button
            type="button"
            onClick={async () => {
              try {
                const mascot = new Window('mascot');
                await mascot.show();
                await getCurrentWindow().hide();
              } catch (e) { console.error('Could not switch to mascot', e); }
            }}
            className="flex h-9 w-full items-center justify-between rounded-[var(--p-radius-sm)] border border-[var(--b1)] bg-[var(--bg-hover)] px-3 text-xs font-medium text-[var(--t2)] transition-all duration-150 hover:border-[var(--b2)] hover:bg-[var(--p-accent-soft)] hover:text-[var(--p-accent)] shadow-[inset_0_1px_0_var(--p-inset-hi)]"
          >
            <span className="flex items-center gap-2"><Heart size={13} strokeWidth={1.8} /> Keep Aiko on desktop</span>
            <ExternalLink size={12} className="opacity-50" />
          </button>

          {/* Companion settings */}
          <details className="group rounded-[var(--p-radius-sm)] border border-[var(--b1)] bg-[var(--bg-hover)] shadow-[inset_0_1px_0_var(--p-inset-hi)]">
            <summary className="flex cursor-pointer list-none items-center justify-between px-3 py-2.5 text-xs text-[var(--t3)] outline-none transition hover:text-[var(--t1)] focus-visible:ring-2 focus-visible:ring-[var(--p-accent)]/40 [&::-webkit-details-marker]:hidden">
              <span className="flex items-center gap-2"><SlidersHorizontal size={12} strokeWidth={1.8} /> Companion settings</span>
              <ChevronDown size={13} className="transition-transform group-open:rotate-180" />
            </summary>
            <div className="space-y-3 border-t border-[var(--b1)] p-3">
              <div className="flex items-center justify-between gap-3 text-xs">
                <span className="text-[var(--t4)]">Model</span>
                <span className="max-w-[150px] truncate text-right text-[var(--t2)]" title={apiConfig.model}>{apiConfig.model}</span>
              </div>
              <div className="flex items-center justify-between gap-3 text-xs">
                <span className="text-[var(--t4)]">Provider</span>
                <span className="text-right text-[var(--t2)]">{apiConfig.provider}</span>
              </div>
              <label className="block pt-1">
                <span className="mb-2 flex items-center justify-between text-xs text-[var(--t4)]">
                  <span>Avatar size</span>
                  <span className="text-[var(--t2)]">{Math.round(avatarScale * 100)}%</span>
                </span>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.05"
                  value={avatarScale}
                  onChange={(event) => setAvatarScale(parseFloat(event.target.value))}
                  className="w-full accent-[var(--p-accent)]"
                  aria-label="Adjust avatar size"
                />
              </label>
              <NeuralControlPanel />
            </div>
          </details>
        </div>
      )}
    </aside>
  );
}
