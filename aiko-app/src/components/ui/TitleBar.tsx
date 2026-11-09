import React, { useEffect, useState, useRef } from 'react';
import { getCurrentWindow, LogicalSize } from '@tauri-apps/api/window';
import { invoke } from '@tauri-apps/api/core';
import {
  PanelLeft,
  Minus,
  Square,
  X,
  Settings2,
  LayoutTemplate,
  Columns,
  PictureInPicture2,
  Activity,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Volume2,
  Brain,
  Database,
  Eye,
} from 'lucide-react';
import { RotatingOrbital } from '../AnimatedIcons';
import { useNeuralStore, resolveHubUrl, getAuthHeaders, getHubUrl } from '../../store/useNeuralStore';

interface TitleBarProps {
  sessionLabel: string;
  showAnimatedAssets: boolean;
  onSettings: () => void;
  onToggleSidebar: () => void;
  onOpenDiagnostics?: () => void;
}

interface HubHealthInfo {
  status: 'healthy' | 'degraded' | 'offline';
  llm_provider?: string;
  llm_model?: string;
  llm_fallback?: string | null;
  llm_url?: string;
  has_api_key?: boolean;
  tts_enabled?: boolean;
  tts_voice?: string;
  memory_ok?: boolean;
  rag_available?: boolean;
  bridges?: Record<string, string>;
}

export function TitleBar({ sessionLabel, showAnimatedAssets, onSettings, onToggleSidebar, onOpenDiagnostics }: TitleBarProps) {
  const isTauri = !!(window as any).__TAURI__;
  const layoutMode = useNeuralStore((s) => s.layoutMode);
  const setLayoutMode = useNeuralStore((s) => s.setLayoutMode);
  const bridgeStatus = useNeuralStore((s) => s.bridgeStatus);
  const apiConfig = useNeuralStore((s) => s.apiConfig);
  const connect = useNeuralStore((s) => s.connect);
  const fetchSettings = useNeuralStore((s) => s.fetchSettings);

  const [health, setHealth] = useState<HubHealthInfo>({ status: 'offline' });
  const [healthOpen, setHealthOpen] = useState(false);
  const [reloading, setReloading] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  const pollHealth = async () => {
    try {
      const hubUrl = await resolveHubUrl();
      const res = await fetch(`${hubUrl}/health`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setHealth({
        status: data.status === 'healthy' ? 'healthy' : 'degraded',
        llm_provider: data.llm_provider,
        llm_model: data.llm_model,
        llm_fallback: data.llm_fallback,
        llm_url: data.llm_url,
        has_api_key: data.has_api_key,
        tts_enabled: data.tts_enabled,
        tts_voice: data.tts_voice,
        memory_ok: data.memory_ok ?? true,
        rag_available: data.rag_available ?? false,
        bridges: data.bridges || {},
      });
    } catch (_) {
      setHealth({ status: 'offline' });
    }
  };

  useEffect(() => {
    void pollHealth();
    const timer = window.setInterval(() => void pollHealth(), 10000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setHealthOpen(false);
      }
    };
    if (healthOpen) {
      document.addEventListener('mousedown', onClickOutside);
    }
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, [healthOpen]);

  const handleReconnectAndReload = async () => {
    setReloading(true);
    try {
      const hubUrl = await resolveHubUrl();
      const headers = await getAuthHeaders();
      await fetch(`${hubUrl}/api/settings/reload`, { method: 'POST', headers }).catch(() => {});
      await fetchSettings();
      connect(getHubUrl());
      await pollHealth();
    } finally {
      setReloading(false);
    }
  };

  const minimize = () => isTauri ? getCurrentWindow().minimize().catch(console.error) : undefined;
  const maximize = () => isTauri ? getCurrentWindow().toggleMaximize().catch(console.error) : undefined;
  const close = () => isTauri ? getCurrentWindow().hide().catch(console.error) : window.close();

  const handleDesktopPetMode = async () => {
    if (isTauri) {
      try {
        await invoke('switch_to_mascot');
        return;
      } catch (err) {
        console.warn('[Aiko] switch_to_mascot command fallback:', err);
        try {
          const win = getCurrentWindow();
          await win.setAlwaysOnTop(true);
          await win.setSize(new LogicalSize(320, 460));
        } catch (_) {}
        window.location.href = '/?mascot=1';
        return;
      }
    }
    const popup = window.open(
      '/?mascot=1',
      'AikoDesktopPet',
      'width=320,height=460,menubar=no,toolbar=no,location=no,status=no,resizable=yes'
    );
    if (!popup) {
      window.location.href = '/?mascot=1';
    }
  };

  const noDrag = { WebkitAppRegion: 'no-drag' } as React.CSSProperties;

  const wsConnected = bridgeStatus?.status === 'connected';
  const activeModel = health.llm_model || apiConfig?.model || 'gemma4:31b-cloud';
  const activeProvider = health.llm_provider || apiConfig?.provider || 'Ollama';
  const overallState: 'green' | 'amber' | 'red' =
    health.status === 'offline'
      ? 'red'
      : !wsConnected
      ? 'amber'
      : 'green';

  const dotColor =
    overallState === 'green'
      ? '#10b981'
      : overallState === 'amber'
      ? '#f59e0b'
      : '#ef4444';

  return (
    <header
      data-tauri-drag-region
      className="h-11 bg-[var(--bg-base)] flex items-center justify-between shrink-0 border-b border-[var(--b1)] select-none px-2 z-30 relative"
      style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}
    >
      {/* Left: Navigation & Layout Mode */}
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

        <button
          onClick={() => setLayoutMode(layoutMode === 'cinematic' ? 'classic' : 'cinematic')}
          title={layoutMode === 'cinematic' ? 'Switch to Classic Chat Focus' : 'Switch to Cinematic Stage (70:30 Hero Ratio)'}
          aria-label="Toggle Layout Mode"
          className={`w-8 h-8 rounded-lg border cursor-pointer flex items-center justify-center transition-all duration-150 shrink-0 ${
            layoutMode === 'cinematic'
              ? 'text-[var(--accent)] border-[var(--accent)]/30 bg-[var(--accent)]/10'
              : 'text-[var(--t3)] border-transparent hover:text-[var(--t1)] hover:bg-[var(--bg-hover)]'
          }`}
          style={noDrag}
        >
          {layoutMode === 'cinematic' ? (
            <LayoutTemplate size={14} strokeWidth={1.8} />
          ) : (
            <Columns size={14} strokeWidth={1.8} />
          )}
        </button>

        <button
          onClick={handleDesktopPetMode}
          title="Desktop Pet Mode (Always-On-Top Floating Companion)"
          aria-label="Desktop Pet Mode"
          className="h-8 px-2.5 rounded-lg border border-transparent hover:border-[var(--accent)]/35 hover:bg-[var(--accent)]/10 cursor-pointer flex items-center gap-1.5 text-[var(--t3)] hover:text-[var(--accent)] transition-all duration-150 shrink-0"
          style={noDrag}
        >
          <PictureInPicture2 size={14} strokeWidth={1.8} />
          <span className="text-[11px] font-medium hidden md:inline">Pet Mode</span>
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

      {/* Right: Live Health Pill, Settings & Window Controls */}
      <div className="flex items-center gap-1.5" style={noDrag} ref={popoverRef}>
        {/* OpenAmika-style Live Health Indicator Pill */}
        <button
          type="button"
          onClick={() => {
            void pollHealth();
            setHealthOpen((v) => !v);
          }}
          title="System Health: Hub • Brain • Voice • Memory (click for diagnostics)"
          className="flex items-center gap-2 px-2.5 py-1 rounded-full border border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.07] hover:border-white/[0.15] transition-all cursor-pointer"
          style={noDrag}
        >
          <span
            className="w-2 h-2 rounded-full shrink-0"
            style={{
              backgroundColor: dotColor,
              boxShadow: `0 0 8px ${dotColor}`,
            }}
          />
          <span className="text-[11px] font-mono text-[var(--t2)] max-w-[160px] truncate hidden sm:inline">
            {overallState === 'red' ? 'Hub Offline' : `${activeModel}`}
          </span>
        </button>

        {/* Diagnostic Popover */}
        {healthOpen && (
          <div
            className="absolute right-12 top-11 w-80 rounded-2xl border border-white/10 bg-[#14111d]/95 backdrop-blur-xl p-4 shadow-2xl z-50 text-left"
            style={noDrag}
          >
            <div className="flex items-center justify-between pb-2.5 mb-3 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-[var(--accent)]" />
                <span className="text-xs font-bold text-white tracking-wide">Aiko System Health</span>
              </div>
              <button
                type="button"
                onClick={handleReconnectAndReload}
                disabled={reloading}
                className="flex items-center gap-1 px-2 py-1 rounded-md bg-white/[0.06] hover:bg-white/[0.12] text-[10px] font-medium text-white/90 transition-colors cursor-pointer"
              >
                <RefreshCw size={11} className={reloading ? 'animate-spin' : ''} />
                {reloading ? 'Syncing...' : 'Reconnect'}
              </button>
            </div>

            <div className="space-y-2.5 text-[11.5px]">
              {/* Neural Hub & WebSocket */}
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-white/70">
                  {health.status !== 'offline' && wsConnected ? (
                    <CheckCircle2 size={13} className="text-emerald-400" />
                  ) : (
                    <AlertCircle size={13} className="text-amber-400" />
                  )}
                  Neural Hub & Stream
                </span>
                <span className="font-mono text-[11px] text-white/90">
                  {health.status === 'offline' ? 'Unreachable' : wsConnected ? 'Connected' : 'Reconnecting'}
                </span>
              </div>

              {/* Brain / LLM */}
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-white/70">
                  <Brain size={13} className="text-[var(--accent)]" />
                  Brain ({activeProvider})
                </span>
                <span className="font-mono text-[11px] text-emerald-300 truncate max-w-[140px]" title={activeModel}>
                  {activeModel}
                </span>
              </div>

              {/* Backup Model */}
              <div className="flex items-center justify-between">
                <span className="text-white/50 pl-5 text-[11px]">Backup Model</span>
                <span className="font-mono text-[10.5px] text-white/65">
                  {health.llm_fallback || 'Auto (Local Ollama)'}
                </span>
              </div>

              {/* Voice / TTS */}
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-white/70">
                  <Volume2 size={13} className="text-sky-400" />
                  Voice (TTS)
                </span>
                <span className="font-mono text-[11px] text-white/80">
                  {health.tts_enabled ? `Ready (${health.tts_voice || 'vivian'})` : 'Muted in Settings'}
                </span>
              </div>

              {/* Memory */}
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-white/70">
                  <Database size={13} className="text-purple-400" />
                  Long-Term Memory
                </span>
                <span className="font-mono text-[11px] text-white/80">
                  {health.memory_ok ? (health.rag_available ? 'Palace + RAG Active' : 'Active (Local JSON)') : 'Offline'}
                </span>
              </div>

              {/* Vision */}
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-white/70">
                  <Eye size={13} className="text-pink-400" />
                  Screen Vision & PC Helper
                </span>
                <span className="font-mono text-[11px] text-white/80">
                  {health.bridges?.vision === 'online' ? 'Ready' : 'Standby'}
                </span>
              </div>
            </div>

            {overallState !== 'green' && (
              <div className="mt-3 p-2 rounded-lg bg-amber-500/10 border border-amber-500/25 text-[11px] text-amber-200 leading-relaxed">
                {health.status === 'offline'
                  ? 'Neural Hub is not running on port 8000. Run LAUNCH_AIKO.bat to start Aiko.'
                  : 'WebSocket stream is reconnecting. Click Reconnect above if it takes more than 5 seconds.'}
              </div>
            )}

            {onOpenDiagnostics && (
              <button
                type="button"
                onClick={() => {
                  setHealthOpen(false);
                  onOpenDiagnostics();
                }}
                className="w-full mt-3 py-1.5 px-3 rounded-lg bg-[var(--accent)]/15 hover:bg-[var(--accent)]/25 border border-[var(--accent)]/30 text-[11px] font-medium text-white flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
              >
                <Activity size={12} className="text-[var(--accent)]" />
                Open Diagnostics & Performance
              </button>
            )}
          </div>
        )}

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
