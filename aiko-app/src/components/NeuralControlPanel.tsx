import React, { useState } from 'react';
import { useNeuralStore } from '../store/useNeuralStore';
import { Zap, Sparkles, BrainCircuit, Eye } from 'lucide-react';

export function NeuralControlPanel() {
  const store = useNeuralStore();
  const {
    chemicals,
    manualOverrideEnabled,
    visionStreamActive,
    updateChemicals,
    updateIntensityScalers,
    setManualOverrideEnabled,
    toggleVisionStream
  } = store;

  const [activeTab, setActiveTab] = useState<'chemicals' | 'animations'>('chemicals');

  const chemicalMeta = [
    { key: 'dopamine', label: 'Dopamine', desc: 'Joy & Reward', color: 'var(--accent)' },
    { key: 'serotonin', label: 'Serotonin', desc: 'Calm & Affection', color: 'var(--accent)' },
    { key: 'cortisol', label: 'Cortisol', desc: 'Stress & Anger', color: '#9B8C9C' },
    { key: 'adrenaline', label: 'Adrenaline', desc: 'Fear & Action', color: 'var(--accent)' },
    { key: 'oxytocin', label: 'Oxytocin', desc: 'Bonding & Warmth', color: 'var(--accent)' },
    { key: 'melatonin', label: 'Melatonin', desc: 'Drowsiness & Sleep', color: '#9B8C9C' }
  ] as const;

  const scalerMeta = [
    { key: 'jitterIntensity', label: 'Jitter', desc: 'Nervous shaking', step: 0.05, max: 2.0 },
    { key: 'tearIntensity', label: 'Tears', desc: 'Crying volume', step: 0.05, max: 2.0 },
    { key: 'leanIntensity', label: 'Interest', desc: 'Forward lean depth', step: 0.05, max: 2.0 },
    { key: 'blushIntensity', label: 'Blush', desc: 'Cheek saturation', step: 0.05, max: 2.0 },
    { key: 'poutIntensity', label: 'Pout', desc: 'Lip pouting', step: 0.05, max: 2.0 },
    { key: 'bobaIntensity', label: 'Wobble', desc: 'Idle physics', step: 0.05, max: 2.0 },
    { key: 'oxytocinIntensity', label: 'Tilt', desc: 'Head tilt angle', step: 0.05, max: 2.0 },
    { key: 'melatoninIntensity', label: 'Sleepiness', desc: 'Eyelid heaviness', step: 0.05, max: 2.0 }
  ] as const;

  return (
    <div className="bg-[var(--bg-surface)] border border-white/[0.06] rounded-xl p-4 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.04] pb-3">
        <div className="flex items-center gap-2">
          <BrainCircuit size={14} className="text-[var(--accent)]" />
          <span className="text-[13px] font-semibold text-[#f0ebe3]">
            Neural Control
          </span>
        </div>
        
        <button
          onClick={() => setManualOverrideEnabled(!manualOverrideEnabled)}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium transition-all duration-200 border ${
            manualOverrideEnabled
              ? 'bg-[var(--accent)]/10 border-[var(--accent)]/30 text-[var(--accent)]'
              : 'bg-white/5 border-white/10 text-[#9a8f7e] hover:text-white'
          }`}
        >
          <Zap size={11} />
          {manualOverrideEnabled ? 'Override' : 'Synced'}
        </button>
      </div>

      {/* Vision Stream Toggle */}
      <div className="flex items-center justify-between bg-black/20 border border-white/[0.03] rounded-lg p-3">
        <div className="flex items-center gap-2">
          <Eye size={14} className="text-[#9a8f7e]" />
          <div className="flex flex-col gap-0.5">
            <span className="text-[12px] font-medium text-[#f0ebe3]">Vision Stream</span>
            <span className="text-[11px] text-[#5a5248]">Observes window every 12s</span>
          </div>
        </div>
        <button
          onClick={() => toggleVisionStream(!visionStreamActive)}
          className={`relative w-9 h-5 rounded-full transition-all duration-200 border ${
            visionStreamActive 
              ? 'bg-[var(--accent)]/25 border-[var(--accent)]/50' 
              : 'bg-white/5 border-white/10'
          }`}
        >
          <span 
            className={`absolute top-0.5 left-0.5 w-3.5 h-3.5 rounded-full transition-all duration-200 ${
              visionStreamActive 
                ? 'translate-x-4 bg-[var(--accent)]' 
                : 'bg-[#5a5248]'
            }`}
          />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex bg-black/40 rounded-lg p-0.5 border border-white/[0.03]">
        <button
          onClick={() => setActiveTab('chemicals')}
          className={`flex-1 py-1.5 rounded-md text-[12px] font-medium transition-all ${
            activeTab === 'chemicals'
              ? 'bg-white/[0.05] text-[#f0ebe3]'
              : 'text-[#5a5248] hover:text-[#9a8f7e]'
          }`}
        >
          Neurotransmitters
        </button>
        <button
          onClick={() => setActiveTab('animations')}
          className={`flex-1 py-1.5 rounded-md text-[12px] font-medium transition-all ${
            activeTab === 'animations'
              ? 'bg-white/[0.05] text-[#f0ebe3]'
              : 'text-[#5a5248] hover:text-[#9a8f7e]'
          }`}
        >
          Animation
        </button>
      </div>

      {/* Content */}
      <div className="flex flex-col gap-3 max-h-[240px] overflow-y-auto pr-1 custom-scrollbar">
        {activeTab === 'chemicals' ? (
          <>
            {manualOverrideEnabled && (
              <div className="bg-[var(--accent)]/5 border border-[var(--accent)]/10 rounded-md p-2 text-[11px] text-[var(--accent)]/80 leading-normal flex items-start gap-2">
                <Sparkles size={12} className="text-[var(--accent)] shrink-0 mt-0.5" />
                <span>Override active. Slide levels to trigger real-time emotional behaviors.</span>
              </div>
            )}
            
            {chemicalMeta.map(({ key, label, desc, color }) => {
              const val = chemicals[key] ?? 0.5;
              return (
                <div key={key} className="flex flex-col gap-1.5">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color, opacity: 0.3 + val * 0.7 }} />
                      <span className="text-[12px] font-medium text-[#f0ebe3]">{label}</span>
                      <span className="text-[11px] text-[#5a5248]">{desc}</span>
                    </div>
                    <span className="text-[11px] font-mono text-[#9a8f7e]">{Math.round(val * 100)}%</span>
                  </div>
                  
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.01"
                    disabled={!manualOverrideEnabled}
                    value={val}
                    onChange={(e) => updateChemicals({ [key]: parseFloat(e.target.value) })}
                    className={`w-full h-1.5 rounded-full appearance-none bg-white/5 transition-opacity duration-200 ${
                      manualOverrideEnabled ? 'cursor-pointer hover:bg-white/10' : 'opacity-40 cursor-not-allowed'
                    }`}
                    style={{
                      accentColor: color
                    } as React.CSSProperties}
                  />
                </div>
              );
            })}
          </>
        ) : (
          <>
            {scalerMeta.map(({ key, label, desc, step, max }) => {
              const val = (store as any)[key] ?? 1.0;
              return (
                <div key={key} className="flex flex-col gap-1.5">
                  <div className="flex justify-between items-center">
                    <div className="flex flex-col">
                      <span className="text-[12px] font-medium text-[#f0ebe3]">{label}</span>
                      <span className="text-[11px] text-[#5a5248]">{desc}</span>
                    </div>
                    <span className="text-[11px] font-mono text-[var(--accent)]">{Math.round(val * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0.0"
                    max={max}
                    step={step}
                    value={val}
                    onChange={(e) => updateIntensityScalers({ [key]: parseFloat(e.target.value) })}
                    className="w-full h-1.5 bg-white/5 rounded-full appearance-none cursor-pointer hover:bg-white/10"
                    style={{ accentColor: 'var(--accent)' } as React.CSSProperties}
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
