import React, { useState } from 'react';
import { useNeuralStore } from '../store/useNeuralStore';
import { Zap, Sparkles, BrainCircuit } from 'lucide-react';

export function NeuralControlPanel() {
  const {
    chemicals,
    manualOverrideEnabled,
    visionStreamActive,
    updateChemicals,
    updateIntensityScalers,
    setManualOverrideEnabled,
    toggleVisionStream
  } = useNeuralStore();

  const [activeTab, setActiveTab] = useState<'chemicals' | 'animations'>('chemicals');

  const chemicalMeta = [
    { key: 'dopamine', label: 'Dopamine', desc: 'Joy & Reward', color: '#f59e0b', glow: 'rgba(245,158,11,0.2)' },
    { key: 'serotonin', label: 'Serotonin', desc: 'Calm & Affection', color: '#10b981', glow: 'rgba(16,185,129,0.2)' },
    { key: 'cortisol', label: 'Cortisol', desc: 'Stress & Anger', color: '#ef4444', glow: 'rgba(239,68,68,0.2)' },
    { key: 'adrenaline', label: 'Adrenaline', desc: 'Fear & Action', color: '#ec4899', glow: 'rgba(236,72,153,0.2)' },
    { key: 'oxytocin', label: 'Oxytocin', desc: 'Bonding & Warmth', color: '#a855f7', glow: 'rgba(168,85,247,0.2)' },
    { key: 'melatonin', label: 'Melatonin', desc: 'Drowsiness & Sleep', color: '#3b82f6', glow: 'rgba(59,130,246,0.2)' }
  ] as const;

  const scalerMeta = [
    { key: 'jitterIntensity', label: 'Jitter Sensitivity', desc: 'Nervous/Panic somatic body shaking', step: 0.05, max: 2.0 },
    { key: 'tearIntensity', label: 'Tear Overflow', desc: 'Crying frequency and tear flow volume', step: 0.05, max: 2.0 },
    { key: 'leanIntensity', label: 'Interest Leaning', desc: 'Physical forward-lean depth', step: 0.05, max: 2.0 },
    { key: 'blushIntensity', label: 'Cheek Blush Glow', desc: 'Cheek blush saturation overlay', step: 0.05, max: 2.0 },
    { key: 'poutIntensity', label: 'Pout & Cheek-Puff', desc: 'Cheek puffing and lip pouting', step: 0.05, max: 2.0 },
    { key: 'bobaIntensity', label: 'Boba Wobble/Sway', desc: 'Idle dynamic wobbling physics', step: 0.05, max: 2.0 },
    { key: 'oxytocinIntensity', label: 'Oxytocin Tilt multiplier', desc: 'Head-tilt angle scaling', step: 0.05, max: 2.0 },
    { key: 'melatoninIntensity', label: 'Melatonin Sleepiness', desc: 'Eyelid heaviness & drowsiness scale', step: 0.05, max: 2.0 }
  ] as const;

  return (
    <div className="bg-[rgba(212,149,106,0.03)] border border-[rgba(212,149,106,0.1)] rounded-xl p-3 flex flex-col gap-3 backdrop-blur-md">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.04] pb-2">
        <div className="flex items-center gap-1.5">
          <BrainCircuit size={13} className="text-[var(--acc)] animate-pulse" />
          <span className="text-[9px] uppercase font-black tracking-widest text-[rgba(212,149,106,0.8)]">
            Neural Control Deck
          </span>
        </div>
        
        {/* Toggle Manual Override */}
        <button
          onClick={() => setManualOverrideEnabled(!manualOverrideEnabled)}
          className={`flex items-center gap-1 px-2 py-0.5 rounded text-[8px] font-bold uppercase transition-all duration-300 border ${
            manualOverrideEnabled
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.15)] animate-pulse'
              : 'bg-white/5 border-white/10 text-slate-400 hover:text-white'
          }`}
          title={manualOverrideEnabled ? 'Click to Sync with Backend' : 'Click to Manually Tweak'}
        >
          <Zap size={9} />
          {manualOverrideEnabled ? 'Override' : 'Synced'}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex bg-black/40 rounded-lg p-0.5 border border-white/[0.03]">
        <button
          onClick={() => setActiveTab('chemicals')}
          className={`flex-1 py-1 rounded-md text-[8px] font-bold uppercase tracking-wider transition-all ${
            activeTab === 'chemicals'
              ? 'bg-white/[0.05] text-white shadow-inner'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Neurotransmitters
        </button>
        <button
          onClick={() => setActiveTab('animations')}
          className={`flex-1 py-1 rounded-md text-[8px] font-bold uppercase tracking-wider transition-all ${
            activeTab === 'animations'
              ? 'bg-white/[0.05] text-white shadow-inner'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Animation Scalers
        </button>
      </div>

      {/* Vision Stream Mode Switch */}
      <div className="flex items-center justify-between bg-black/20 border border-white/[0.03] rounded-lg p-2 transition-all duration-300 hover:border-[rgba(212,149,106,0.2)]">
        <div className="flex flex-col gap-0.5">
          <span className="text-[9px] font-bold text-white uppercase tracking-wider">📺 Vision Stream Mode</span>
          <span className="text-[6.5px] text-slate-500 font-sans leading-none">Observes active window every 12 seconds</span>
        </div>
        <button
          onClick={() => toggleVisionStream(!visionStreamActive)}
          className={`relative w-8 h-4 rounded-full transition-all duration-300 border ${
            visionStreamActive 
              ? 'bg-[var(--acc)]/25 border-[var(--acc)]/50 shadow-[0_0_8px_var(--acc)]' 
              : 'bg-white/5 border-white/10'
          }`}
        >
          <span 
            className={`absolute top-0.5 left-0.5 w-2.5 h-2.5 rounded-full transition-all duration-300 ${
              visionStreamActive 
                ? 'translate-x-4 bg-[var(--acc)] shadow-[0_0_4px_var(--acc)]' 
                : 'bg-slate-500'
            }`}
          />
        </button>
      </div>

      {/* Content */}
      <div className="flex flex-col gap-2.5 max-h-[220px] overflow-y-auto pr-1 custom-scrollbar">
        {activeTab === 'chemicals' ? (
          <>
            {manualOverrideEnabled && (
              <div className="bg-amber-500/5 border border-amber-500/10 rounded-md p-1.5 text-[8px] text-amber-300/80 leading-normal mb-1 flex items-start gap-1">
                <Sparkles size={11} className="text-amber-400 shrink-0 mt-0.5" />
                <span>Override Active! Slide levels to trigger real-time emotional behaviors and expression responses.</span>
              </div>
            )}
            
            {chemicalMeta.map(({ key, label, desc, color, glow }) => {
              const val = chemicals[key] ?? 0.5;
              return (
                <div key={key} className="flex flex-col gap-1">
                  <div className="flex justify-between items-center text-[8px] font-bold tracking-wide uppercase">
                    <span className="flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}` }} />
                      <span className="text-white">{label}</span>
                      <span className="text-slate-500 text-[7px] font-medium font-sans">({desc})</span>
                    </span>
                    <span style={{ color }} className="font-mono text-[9px]">{Math.round(val * 100)}%</span>
                  </div>
                  
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.01"
                    disabled={!manualOverrideEnabled}
                    value={val}
                    onChange={(e) => updateChemicals({ [key]: parseFloat(e.target.value) })}
                    style={{
                      '--thumb-color': color,
                      '--thumb-glow': glow
                    } as React.CSSProperties}
                    className={`w-full h-1 rounded appearance-none bg-white/5 transition-opacity duration-200 ${
                      manualOverrideEnabled ? 'cursor-pointer hover:bg-white/10' : 'opacity-50 cursor-not-allowed'
                    }`}
                  />
                </div>
              );
            })}
          </>
        ) : (
          <>
            {scalerMeta.map(({ key, label, desc, step, max }) => {
              const val = (useNeuralStore() as any)[key] ?? 1.0;
              return (
                <div key={key} className="flex flex-col gap-1">
                  <div className="flex justify-between items-center text-[8px] font-bold tracking-wide uppercase">
                    <span className="flex flex-col">
                      <span className="text-white">{label}</span>
                      <span className="text-slate-500 text-[6.5px] font-sans lowercase leading-none">{desc}</span>
                    </span>
                    <span className="text-[var(--acc)] font-mono text-[9px]">{Math.round(val * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0.0"
                    max={max}
                    step={step}
                    value={val}
                    onChange={(e) => updateIntensityScalers({ [key]: parseFloat(e.target.value) })}
                    className="w-full h-1 bg-white/5 rounded appearance-none cursor-pointer hover:bg-white/10 accent-[var(--acc)]"
                  />
                </div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
}
