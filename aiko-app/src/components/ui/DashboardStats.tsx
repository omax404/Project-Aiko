import { Window, getCurrentWindow } from '@tauri-apps/api/window';
import { ExternalLink } from 'lucide-react';
import { GothicButton } from '../GothicButton';
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
  amplitude: number;
  chemicals: any;
  isCompact?: boolean;
}

export function DashboardStats({
  bridgeStatus, isThinking, isTalking, currentEmotion,
  avatarScale, setAvatarScale, amplitude, chemicals, isCompact
}: DashboardStatsProps) {
  const apiConfig = useNeuralStore(state => state.apiConfig);
  const width = isCompact ? 160 : 320;

  return (
    <div
      className="h-full flex flex-col bg-[var(--bg-sidebar)] border-l border-[var(--b1)] overflow-hidden transition-all duration-300"
      style={{ width: `${width}px`, minWidth: `${width}px` }}
    >
      {/* Live2D Avatar — scaled up */}
      <div className="flex-1 flex items-center justify-center bg-black/30 relative overflow-hidden min-h-0">
        <Live2DAvatar
          modelUrl="/live2d/vivian/vivian.model3.json"
          isThinking={isThinking}
          isTalking={isTalking}
          emotion={currentEmotion}
          width={width}
          height={isCompact ? 300 : 600}
          scale={isCompact ? avatarScale * 0.65 : avatarScale}
          amplitude={amplitude}
          chemicals={chemicals}
          offsetX={35}
          offsetY={50}
        />
        {/* Online dot */}
        <div className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,1)]" />
      </div>

      {/* Stats — bottom section */}
      {!isCompact && (
        <div className="px-3.5 pb-4 pt-3.5 flex flex-col gap-2.5 overflow-y-auto max-h-[450px] shrink-0 custom-scrollbar">
          <div className="w-full my-1">
            <div className="flex items-center gap-3 w-full opacity-40 select-none pointer-events-none">
              <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[var(--acc)]/30 to-transparent" />
              <div className="w-1.5 h-1.5 rotate-45 border border-[var(--acc)]/30" />
              <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[var(--acc)]/30 to-transparent" />
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div className="text-[11px] font-bold text-[var(--t2)] tracking-[2px] uppercase">
              System Core
            </div>
          </div>

          {/* Mascot Mode Toggle */}
          <button
            onClick={async () => {
              try {
                const mascot = new Window('mascot');
                await mascot.show();
                await getCurrentWindow().hide();
              } catch (e) { console.error("Could not switch to mascot", e); }
            }}
            className="bg-[var(--acc-soft)] border border-[var(--acc)] rounded-lg p-2 px-3 flex items-center justify-between hover:bg-[var(--acc)] hover:text-black transition-all group w-full text-left cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <GothicButton icon="rose" size="sm" className="pointer-events-none group-hover:ring-1 group-hover:ring-black" />
              <span className="text-[12px] uppercase font-bold tracking-widest text-[var(--acc)] group-hover:text-black">Mascot Mode</span>
            </div>
            <ExternalLink size={14} className="text-[var(--acc)] group-hover:text-black" />
          </button>

          {/* Neural Control Deck */}
          <NeuralControlPanel />

          {/* Aiko Brain Chemicals */}
          <div className="bg-[var(--acc-soft)] border border-[var(--b1)] rounded-lg p-2.5 px-3 flex flex-col gap-2.5">
            <div className="text-[11px] text-[var(--t2)] font-semibold uppercase tracking-wider">
              Neuromodulators
            </div>
            <div className="flex flex-col gap-2">
              {[
                { name: 'Dopamine', value: chemicals?.dopamine ?? 50, color: 'bg-yellow-500' },
                { name: 'Serotonin', value: chemicals?.serotonin ?? 50, color: 'bg-green-500' },
                { name: 'Cortisol', value: chemicals?.cortisol ?? 50, color: 'bg-red-500' },
                { name: 'Adrenaline', value: chemicals?.adrenaline ?? 50, color: 'bg-blue-500' },
              ].map((c) => (
                <div key={c.name} className="flex flex-col gap-1">
                  <div className="flex justify-between text-[10px] uppercase font-medium">
                    <span className="text-[var(--t2)]">{c.name}</span>
                    <span className="text-[var(--t1)] font-mono">{c.value}%</span>
                  </div>
                  <div className="w-full h-1 bg-white/[0.05] rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${c.color} transition-all duration-500`} 
                      style={{ width: `${c.value}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Avatar Scale Slider */}
          <div className="bg-[var(--acc-soft)] border border-[var(--b1)] rounded-lg p-2.5 px-3 flex flex-col gap-1.5">
            <div className="flex justify-between items-center">
              <span className="text-[11px] text-[var(--t2)] font-semibold uppercase">Avatar Scale</span>
              <span className="text-[12px] text-[var(--acc)] font-bold font-mono">{(avatarScale * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.05"
              value={avatarScale}
              onChange={(e) => setAvatarScale(parseFloat(e.target.value))}
              className="w-full h-1 bg-[var(--b2)] rounded-lg appearance-none cursor-pointer accent-[var(--acc)]"
              title="Adjust Avatar Scale"
            />
          </div>

          {/* Active Model */}
          <div className="bg-[var(--acc-soft)] border border-[var(--b1)] rounded-lg p-2.5 px-3 flex flex-col gap-1.5">
            <div className="text-[11px] text-[var(--t2)] font-semibold uppercase">Active Model</div>
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-[var(--acc)] animate-pulse" />
              <span className="text-[12px] text-[var(--t1)] font-bold font-mono uppercase truncate">{apiConfig.model}</span>
            </div>
            <div className="text-[11px] text-[var(--t3)] font-bold tracking-widest uppercase">
              {apiConfig.provider} // Active
            </div>
          </div>

          {/* Sync Bridge */}
          <div className="bg-[var(--acc-soft)] border border-[var(--b1)] rounded-lg p-2.5 px-3 flex flex-col gap-1.5">
            <div className="text-[11px] text-[var(--t2)] font-semibold uppercase">Sync Bridge</div>
            <div className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full ${bridgeStatus.status === 'connected' ? 'bg-green-500 shadow-[0_0_6px_#22c55e]' : 'bg-red-500'}`} />
              <span className="text-[12px] text-[var(--t1)] font-bold font-mono uppercase">{bridgeStatus.status}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
