import React from 'react';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { PanelLeft, ChevronLeft, ChevronRight, Minus, Square } from 'lucide-react';
import { GothicButton } from '../GothicButton';
import { RotatingOrbital } from '../AnimatedIcons';

interface TitleBarProps {
  sessionLabel: string;
  showAnimatedAssets: boolean;
  onSettings: () => void;
  onToggleSidebar: () => void;
}

export function TitleBar({ sessionLabel, showAnimatedAssets, onSettings, onToggleSidebar }: TitleBarProps) {
  const isTauri = !!(window as any).__TAURI__;
  const minimize = () => isTauri ? getCurrentWindow().minimize().catch(console.error) : undefined;
  const maximize = () => isTauri ? getCurrentWindow().toggleMaximize().catch(console.error) : undefined;
  const close = () => isTauri ? getCurrentWindow().close().catch(console.error) : window.close();

  const noDrag = { WebkitAppRegion: 'no-drag' } as React.CSSProperties;

  return (
    <div
      data-tauri-drag-region
      className="h-12 bg-[#0e0d0c] flex items-center justify-between shrink-0 border-b border-white/[0.04] select-none"
      style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}
    >
      {/* Left: App icon buttons */}
      <div className="flex items-center" style={noDrag}>
        <button
          onClick={onToggleSidebar}
          title="Toggle Sidebar"
          className="w-10 h-12 bg-transparent border-none cursor-pointer flex items-center justify-center text-white/[0.35] hover:bg-white/[0.07] hover:text-white/80 transition-all duration-100 shrink-0"
          style={noDrag}
        >
          <PanelLeft size={16} />
        </button>
        <div className="flex">
          <button
            onClick={() => {}}
            title="Back"
            className="w-10 h-12 bg-transparent border-none cursor-pointer flex items-center justify-center text-white/[0.35] hover:bg-white/[0.07] hover:text-white/80 transition-all duration-100 shrink-0"
            style={noDrag}
          >
            <ChevronLeft size={18} className="opacity-30" />
          </button>
          <button
            onClick={() => {}}
            title="Forward"
            className="w-10 h-12 bg-transparent border-none cursor-pointer flex items-center justify-center text-white/[0.35] hover:bg-white/[0.07] hover:text-white/80 transition-all duration-100 shrink-0"
            style={noDrag}
          >
            <ChevronRight size={18} className="opacity-30" />
          </button>
        </div>
      </div>

      {/* Center: drag region only */}
      <div
        data-tauri-drag-region
        className="flex-1 flex items-center justify-center gap-2.5 pointer-events-none"
      >
        {showAnimatedAssets ? <RotatingOrbital /> : <div className="w-1.5 h-1.5 rounded-full bg-white/[0.08]" />}
        <span className="text-[11px] text-white/[0.15] font-medium tracking-[0.15em]">
          AIKO — {sessionLabel}
        </span>
      </div>

      {/* Right: action icons + window controls */}
      <div className="flex items-center px-2 gap-1" style={noDrag}>
        <GothicButton
          icon="settings"
          size="sm"
          onClick={onSettings}
          title="Settings"
        />
        <GothicButton
          icon="discord"
          size="sm"
          onClick={() => window.open('https://discord.com', '_blank')}
          title="Discord Community"
        />
        <span className="w-px h-4 bg-white/[0.06] mx-1 shrink-0" />
        <button
          onClick={minimize}
          title="Minimize"
          className="w-9 h-9 bg-transparent border-none cursor-pointer flex items-center justify-center text-white/[0.35] hover:bg-white/[0.08] hover:text-white/90 transition-all duration-100 shrink-0 rounded-lg"
          style={noDrag}
        >
          <Minus size={14} />
        </button>
        <button
          onClick={maximize}
          title="Maximize"
          className="w-9 h-9 bg-transparent border-none cursor-pointer flex items-center justify-center text-white/[0.35] hover:bg-white/[0.08] hover:text-white/90 transition-all duration-100 shrink-0 rounded-lg"
          style={noDrag}
        >
          <Square size={11} />
        </button>
        <GothicButton
          icon="close"
          size="sm"
          onClick={close}
          title="Close"
          className="hover:shadow-red-glow"
        />
      </div>
    </div>
  );
}
