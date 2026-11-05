import React from 'react';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { PanelLeft, Minus, Square, X, Settings2 } from 'lucide-react';
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
  const close = () => isTauri ? getCurrentWindow().hide().catch(console.error) : window.close();

  const noDrag = { WebkitAppRegion: 'no-drag' } as React.CSSProperties;

  return (
    <header
      data-tauri-drag-region
      className="h-11 bg-[var(--bg-base)] flex items-center justify-between shrink-0 border-b border-[var(--b1)] select-none px-2 z-30"
      style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}
    >
      {/* Left: Navigation */}
      <div className="flex items-center gap-1.5" style={noDrag}>
        <button
          onClick={onToggleSidebar}
          title="Toggle Sidebar (Ctrl+B)"
          aria-label="Toggle Sidebar"
          className="w-8 h-8 rounded-lg bg-transparent border border-transparent cursor-pointer flex items-center justify-center text-[var(--t3)] hover:text-[var(--t1)] hover:bg-[var(--bg-hover)] hover:border-[var(--b1)] transition-all duration-150 shrink-0"
          style={noDrag}
        >
          <PanelLeft size={15} strokeWidth={1.8} />
        </button>
      </div>

      {/* Center: Window title & session telemetry */}
      <div
        data-tauri-drag-region
        className="flex-1 flex items-center justify-center gap-2 pointer-events-none"
      >
        {showAnimatedAssets ? (
          <RotatingOrbital />
        ) : (
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--p-accent)] opacity-60" />
        )}
        <span className="text-[12px] text-[var(--t3)] font-medium tracking-wide">
          Aiko <span className="text-[var(--t4)] font-mono text-[11px]">· {sessionLabel}</span>
        </span>
      </div>

      {/* Right: Actions & Window Controls */}
      <div className="flex items-center gap-1" style={noDrag}>
        <button
          onClick={onSettings}
          title="Settings"
          aria-label="Settings"
          className="w-8 h-8 rounded-lg bg-transparent border border-transparent cursor-pointer flex items-center justify-center text-[var(--t3)] hover:text-[var(--t1)] hover:bg-[var(--bg-hover)] hover:border-[var(--b1)] transition-all duration-150 shrink-0"
          style={noDrag}
        >
          <Settings2 size={15} strokeWidth={1.8} />
        </button>

        <span className="w-px h-3.5 bg-[var(--b1)] mx-0.5 shrink-0" />

        <button
          onClick={minimize}
          title="Minimize"
          aria-label="Minimize"
          className="w-8 h-8 rounded-lg bg-transparent border border-transparent cursor-pointer flex items-center justify-center text-[var(--t3)] hover:text-[var(--t1)] hover:bg-[var(--bg-hover)] hover:border-[var(--b1)] transition-all duration-150 shrink-0"
          style={noDrag}
        >
          <Minus size={13} strokeWidth={1.8} />
        </button>

        <button
          onClick={maximize}
          title="Maximize"
          aria-label="Maximize"
          className="w-8 h-8 rounded-lg bg-transparent border border-transparent cursor-pointer flex items-center justify-center text-[var(--t3)] hover:text-[var(--t1)] hover:bg-[var(--bg-hover)] hover:border-[var(--b1)] transition-all duration-150 shrink-0"
          style={noDrag}
        >
          <Square size={11} strokeWidth={1.8} />
        </button>

        <button
          onClick={close}
          title="Close"
          aria-label="Close"
          className="w-8 h-8 rounded-lg bg-transparent border border-transparent cursor-pointer flex items-center justify-center text-[var(--t3)] hover:text-[#f87171] hover:bg-[#f87171]/10 hover:border-[#f87171]/20 transition-all duration-150 shrink-0"
          style={noDrag}
        >
          <X size={14} strokeWidth={1.8} />
        </button>
      </div>
    </header>
  );
}
