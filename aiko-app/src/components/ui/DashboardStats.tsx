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
  // Keep high-frequency lip-sync updates scoped to the avatar instead of the chat tree.
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
      className="flex h-full shrink-0 flex-col overflow-hidden border-l border-white/[0.07] bg-[#15121a] transition-[width] duration-300"
      style={{ width: `${width}px`, minWidth: `${width}px` }}
    >
      <div className="relative flex min-h-0 flex-1 items-center justify-center overflow-hidden bg-[radial-gradient(ellipse_at_50%_44%,rgba(184,161,217,0.10),transparent_64%)]">
        <Live2DAvatar
          modelUrl="/live2d/vivian/vivian.model3.json"
          isThinking={isThinking}
          isTalking={isTalking}
          emotion={currentEmotion}
          width={width}
          height={isCompact ? 300 : 560}
          scale={isCompact ? avatarScale * 0.65 : Math.min(avatarScale, 1.15)}
          amplitude={amplitude}
          chemicals={chemicals}
          offsetX={35}
          offsetY={50}
          interactive
        />

        <div className="absolute left-4 top-4 flex items-center gap-2 rounded-full border border-white/[0.08] bg-[#100d14]/75 px-2.5 py-1.5 backdrop-blur">
          <span className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-emerald-400' : 'bg-white/30'}`} />
          <span className="text-[10px] font-medium text-white/65">{connected ? 'Ready to talk' : 'Waiting for Aiko'}</span>
        </div>
      </div>

      {!isCompact && (
        <div className="shrink-0 border-t border-white/[0.07] p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-white">Aiko</p>
              <p className="mt-1 truncate text-xs text-white/45">{isThinking ? 'Thinking…' : isTalking ? 'Speaking' : emotionLabel}</p>
            </div>
            <span className={`shrink-0 rounded-full px-2.5 py-1 text-[10px] ${connected ? 'bg-emerald-400/[0.09] text-emerald-200/80' : 'bg-white/[0.05] text-white/40'}`}>
              {connected ? 'Connected' : 'Offline'}
            </span>
          </div>

          <button
            type="button"
            onClick={async () => {
              try {
                const mascot = new Window('mascot');
                await mascot.show();
                await getCurrentWindow().hide();
              } catch (e) { console.error('Could not switch to mascot', e); }
            }}
            className="mt-4 flex h-10 w-full items-center justify-between rounded-xl border border-[var(--accent)]/20 bg-[var(--accent)]/[0.07] px-3 text-xs font-medium text-[var(--accent)] transition hover:border-[var(--accent)]/35 hover:bg-[var(--accent)]/[0.12]"
          >
            <span className="flex items-center gap-2"><Heart size={14} /> Keep Aiko on your desktop</span>
            <ExternalLink size={13} className="opacity-65" />
          </button>

          <details className="group mt-3 rounded-xl border border-white/[0.07] bg-white/[0.018]">
            <summary className="flex cursor-pointer list-none items-center justify-between px-3 py-3 text-xs text-white/55 outline-none transition hover:text-white/80 focus-visible:ring-2 focus-visible:ring-[var(--accent)]/40 [&::-webkit-details-marker]:hidden">
              <span className="flex items-center gap-2"><SlidersHorizontal size={13} /> Companion settings</span>
              <ChevronDown size={14} className="transition-transform group-open:rotate-180" />
            </summary>
            <div className="space-y-3 border-t border-white/[0.06] p-3">
              <div className="flex items-center justify-between gap-3 text-xs">
                <span className="text-white/45">Model</span>
                <span className="max-w-[150px] truncate text-right text-white/70" title={apiConfig.model}>{apiConfig.model}</span>
              </div>
              <div className="flex items-center justify-between gap-3 text-xs">
                <span className="text-white/45">Provider</span>
                <span className="text-right text-white/70">{apiConfig.provider}</span>
              </div>
              <label className="block pt-1">
                <span className="mb-2 flex items-center justify-between text-xs text-white/45">
                  <span>Avatar size</span><span className="text-white/70">{Math.round(avatarScale * 100)}%</span>
                </span>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.05"
                  value={avatarScale}
                  onChange={(event) => setAvatarScale(parseFloat(event.target.value))}
                  className="w-full accent-[var(--accent)]"
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
