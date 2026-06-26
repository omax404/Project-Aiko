import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { emit } from '@tauri-apps/api/event';
import { Sidebar } from './components/Sidebar';
import { OnboardingWizard } from './components/OnboardingWizard';
import { ChatBubble } from './components/ChatBubble';
import { InputDock } from './components/InputDock';
import { SettingsPanel } from './components/SettingsPanel';
import { SkeletonLoader } from './components/SkeletonLoader';
import { RotatingOrbital } from './components/AnimatedIcons';
import { ProjectIntelligence } from './components/ProjectIntelligence';
import { Live2DAvatar } from './components/Live2DAvatar';
import { NeuralControlPanel } from './components/NeuralControlPanel';
import { ErrorBoundary } from './components/ErrorBoundary';
import { announce, ScreenReaderAnnouncer } from './components/ScreenReaderAnnouncer';
import { SkipLink } from './components/SkipLink';
import { useNeuralStore } from './store/useNeuralStore';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import {
  PanelLeft,
  ChevronLeft,
  ChevronRight,
  Activity,
  Zap,
  ExternalLink,
  Minus,
  Square,
  AlertTriangle
} from 'lucide-react';
import { Window, getCurrentWindow } from '@tauri-apps/api/window';
import { GothicButton } from './components/GothicButton';


/* ── Custom TitleBar ─────────────────────────────────────── */
function TitleBar({ sessionLabel, showAnimatedAssets, onSettings, onProject, onToggleSidebar }: {
  sessionLabel: string;
  showAnimatedAssets: boolean;
  onSettings: () => void;
  onProject: () => void;
  onToggleSidebar: () => void;
}) {
  const isTauri = !!(window as any).__TAURI__;
  const minimize = () => isTauri ? getCurrentWindow().minimize().catch(console.error) : console.log("Minimize");
  const maximize = () => isTauri ? getCurrentWindow().toggleMaximize().catch(console.error) : console.log("Maximize");
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
        <button
          onClick={onProject}
          title="Project"
          className="w-10 h-12 bg-transparent border-none cursor-pointer flex items-center justify-center text-white/[0.35] hover:bg-white/[0.07] hover:text-white/80 transition-all duration-100 shrink-0"
          style={noDrag}
        >
          <Activity size={14} />
        </button>
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
          className="hover:shadow-[0_0_20px_rgba(239,68,68,0.6)]"
        />
      </div>
    </div>
  );
}

/* ── Right Dashboard (with Live2D inside) ────────────────── */
function DashboardStats({ 
  bridgeStatus, isThinking, isTalking, currentEmotion,
  avatarScale, setAvatarScale, amplitude, chemicals
}: {
  bridgeStatus: any; isThinking: boolean; isTalking: boolean; currentEmotion: string;
  avatarScale: number; setAvatarScale: (s: number) => void; amplitude: number;
  chemicals: any;
}) {
  const { apiConfig } = useNeuralStore();
  return (
    <div className="w-[320px] min-w-[320px] h-full flex flex-col bg-[var(--bg-sidebar)] border-l border-[var(--b1)] overflow-hidden">
      {/* Live2D Avatar — scaled up */}
      <div className="flex-1 flex items-center justify-center bg-black/30 relative overflow-hidden min-h-0">
        <Live2DAvatar
          modelUrl="/live2d/vivian/vivian.model3.json"
          isThinking={isThinking}
          isTalking={isTalking}
          emotion={currentEmotion}
          width={320}
          height={600}
          scale={avatarScale}
          amplitude={amplitude}
          chemicals={chemicals}
        />
        {/* Online dot */}
        <div className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,1)]" />
      </div>

      {/* Stats — bottom section */}
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
          <div className="flex gap-0.5 items-center">
            {[0.4, 0.7, 1.0, 0.6].map((h, i) => (
              <div key={i} className="w-0.5 bg-[var(--acc)]" style={{ height: 10 * h, opacity: 0.5 + h * 0.5 }} />
            ))}
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
    </div>
  );
}

/* ── Welcome Screen ──────────────────────────────────────── */
export function WelcomeScreen({ onRecall }: { onRecall: () => void }) {
  const { dynamicsIntensity } = useNeuralStore();
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: (100 - dynamicsIntensity) / 100 + 0.2 }}
      className="flex-1 flex flex-col items-center justify-center text-center p-12 gap-8"
    >
      <div className="max-w-md">
        <div className="w-full mb-6">
          <div className="flex items-center gap-3 w-full opacity-60 select-none pointer-events-none">
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[var(--acc)]/30 to-transparent" />
            <div className="w-1.5 h-1.5 rotate-45 border border-[var(--acc)]/40" />
            <div className="w-1 h-1 rotate-45 bg-[var(--acc)]/20" />
            <div className="w-1.5 h-1.5 rotate-45 border border-[var(--acc)]/40" />
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[var(--acc)]/30 to-transparent" />
          </div>
        </div>
        <GothicButton icon="rose" size="lg" active className="mx-auto mb-6 pointer-events-none shadow-[0_0_40px_rgba(168,85,247,0.6)]" />
        <h1 className="text-3xl font-bold text-white uppercase brand-text tracking-widest">Aiko</h1>
        <p className="text-[13px] text-slate-500 mt-3 leading-relaxed font-light px-4">
          Your neural companion is ready.
        </p>
      </div>
      <button onClick={onRecall}
        className="px-8 py-3 rounded-xl bg-white/[0.03] border border-white/10 text-[12px] font-bold text-slate-400 uppercase tracking-widest hover:bg-white/5 hover:text-white transition-all">
        View History
      </button>
    </motion.div>
  );
}

/* ── Main App ────────────────────────────────────────────── */
function App() {
  const {
    messages, streamingContent, connect, activeSessionId, sessions,
    isThinking, triggerPurge, loadSessions, fetchBridgeStatus, fetchSettings,
    bridgeStatus, currentEmotion, isSidebarOpen, toggleSidebar, themeColor,
    dynamicsIntensity, showAnimatedAssets, isTalking, avatarScale, setAvatarScale,
    amplitude, apiConfig, chemicals
  } = useNeuralStore();

  const maskUnclosedLatex = (text: string) => {
    // Count occurrences of $$
    const blockMathParts = text.split('$$');
    if (blockMathParts.length % 2 === 0) {
      // Unclosed block math
      blockMathParts[blockMathParts.length - 1] = ' \\dots $$';
      return blockMathParts.join('$$');
    }
    
    // Count occurrences of $
    // Slightly naive, but works for masking
    const inlineMathParts = text.split(/(?<!\\)\$/);
    if (inlineMathParts.length % 2 === 0) {
      inlineMathParts[inlineMathParts.length - 1] = ' \\dots $';
      return inlineMathParts.join('$');
    }
    return text;
  };

  const activeSession = sessions.find(s => s.id === activeSessionId);
  const sessionLabel = activeSession?.title || 'New Session';
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isProjectOpen, setIsProjectOpen] = useState(false);
  const [isPurgeConfirmOpen, setIsPurgeConfirmOpen] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    emit('app-ready').catch(() => { });
    // Inject accent color on mount
    document.documentElement.style.setProperty('--acc', themeColor);
    document.documentElement.style.setProperty('--acc-soft', `${themeColor}1f`);
    document.documentElement.style.setProperty('--acc-glow', `${themeColor}40`);

    try { connect('http://127.0.0.1:8000'); } catch (e) { }
    fetchSettings();
    fetchBridgeStatus();
    loadSessions();
    const t = setInterval(() => {
      fetchBridgeStatus();
      fetchSettings();
    }, 30000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  // Accessibility: Announce thinking state to screen readers
  useEffect(() => {
    if (isThinking) {
      announce('Aiko is thinking', 'polite');
    }
  }, [isThinking]);

  // Accessibility: Announce new messages to screen readers
  const lastMessageCount = useRef(messages.length);
  useEffect(() => {
    if (messages.length > lastMessageCount.current) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg.role === 'assistant') {
        const text = lastMsg.content?.substring(0, 100) || 'Aiko responded';
        announce(`Aiko: ${text}`, 'polite');
      }
    }
    lastMessageCount.current = messages.length;
  }, [messages]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Escape closes any open modal
      if (e.key === 'Escape') {
        if (isSettingsOpen) setIsSettingsOpen(false);
        if (isProjectOpen) setIsProjectOpen(false);
        if (isPurgeConfirmOpen) setIsPurgeConfirmOpen(false);
      }
      // F1 toggles sidebar
      if (e.key === 'F1') {
        e.preventDefault();
        toggleSidebar();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSettingsOpen, isProjectOpen, isPurgeConfirmOpen, toggleSidebar]);

  // Cursor-Follow Glow for Chat Panel
  const chatMouseX = useMotionValue(0);
  const chatMouseY = useMotionValue(0);
  const chatSpringConfig = { stiffness: 120, damping: 20 };
  const chatGlowX = useSpring(chatMouseX, chatSpringConfig);
  const chatGlowY = useSpring(chatMouseY, chatSpringConfig);

  const handleChatMouseMove = (e: React.MouseEvent<HTMLElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    chatMouseX.set(e.clientX - rect.left);
    chatMouseY.set(e.clientY - rect.top);
  };

  return (
    <>
      <SkipLink targetId="main-content" />
      <ScreenReaderAnnouncer />
      <div style={{
      width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column',
      overflow: 'hidden', background: 'var(--bg-base)', color: 'var(--t1)'
    }}>

      {/* ONE titlebar — session name + action icons + window controls */}
      <TitleBar
        sessionLabel={sessionLabel}
        showAnimatedAssets={showAnimatedAssets}
        onSettings={() => setIsSettingsOpen(true)}
        onProject={() => setIsProjectOpen(true)}
        onToggleSidebar={toggleSidebar}
      />

      {/* Onboarding Overlay */}
      {(!apiConfig.apiKey && apiConfig.provider !== 'Ollama') && (
        <div className="absolute inset-0 z-[100]">
          <OnboardingWizard />
        </div>
      )}

      {/* Body row */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* Left sidebar — animated collapse */}
        <AnimatePresence initial={false}>
          {isSidebarOpen && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 280, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{
                type: 'spring',
                damping: 20 + (dynamicsIntensity / 10),
                stiffness: 100 + (dynamicsIntensity / 2)
              }}
              style={{ overflow: 'hidden', flexShrink: 0 }}
            >
              <Sidebar onOpenSettings={() => setIsSettingsOpen(true)} onOpenProject={() => setIsProjectOpen(true)} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Chat area */}
        <main
          id="main-content"
          tabIndex={-1}
          aria-label="Chat conversation"
          onMouseMove={handleChatMouseMove}
          style={{
            flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative',
            background: 'var(--bg-base)'
          }}
          className="group/chat"
        >
          <motion.div
            className="absolute pointer-events-none rounded-full w-60 h-60 bg-[var(--acc-soft)] blur-3xl opacity-0 group-hover/chat:opacity-10 transition-opacity"
            style={{
              x: useTransform(chatGlowX, (v: number) => v - 120),
              y: useTransform(chatGlowY, (v: number) => v - 120),
            }}
          />

          {/* Messages */}
          <div className="flex-1 overflow-y-auto custom-scrollbar" style={{ padding: '24px 24px 0' }}>
            <div style={{ maxWidth: 680, margin: '0 auto', display: 'flex', flexDirection: 'column', paddingBottom: 160 }}>
              {messages.length === 0 ? (
                <WelcomeScreen onRecall={loadSessions} />
              ) : (
                <>
                  <AnimatePresence mode="popLayout" initial={false}>
                    {messages.map((msg: any, i: number) => (
                      <ChatBubble
                        key={(msg.id || msg.timestamp || 'msg') + '-' + i}
                        id={msg.id} role={msg.role} content={msg.content}
                        emotion={msg.emotion} timestamp={msg.timestamp}
                      />
                    ))}
                  </AnimatePresence>

                  {/* Streaming bubble */}
                  <AnimatePresence>
                    {streamingContent && (
                      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                        className="flex w-full mb-12">
                        <div className="flex gap-6 max-w-[85%]">
                          <div className="w-9 h-9 rounded-xl bg-[var(--acc)]/10 border border-[var(--acc)]/30 shadow-[0_0_15px_var(--acc-glow)] flex items-center justify-center flex-shrink-0 mt-1">
                            <Zap size={16} className="text-[var(--acc)] animate-pulse" />
                          </div>
                          <div className="flex flex-col gap-1">
                            <span className="text-[12px] font-bold uppercase tracking-widest text-[var(--acc)] px-1">Aiko</span>
                            <div className="text-[15px] leading-[1.8] text-[var(--t1)] selectable markdown-content">
                              <ReactMarkdown 
                                remarkPlugins={[remarkGfm, remarkMath]}
                                rehypePlugins={[[rehypeKatex, { throwOnError: false }]]}
                                components={{
                                  img: ({ node, src, alt, ...props }) => {
                                    if (!src) return null;
                                    const isSticker = src.includes('/stickers/');
                                    if (isSticker) {
                                      const isTauri = typeof window !== 'undefined' && !!(window as any).__TAURI__;
                                      const hubUrl = isTauri ? 'http://127.0.0.1:8000' : (typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:8000');
                                      const absoluteSrc = src.startsWith('http') ? src : `${hubUrl}${src}`;
                                      return (
                                        <img 
                                          src={absoluteSrc} 
                                          alt={alt || "sticker"} 
                                          className="w-28 h-28 object-contain my-2 inline-block transition-transform hover:scale-110 duration-200 cursor-pointer drop-shadow-[0_4px_12px_rgba(0,0,0,0.15)]"
                                          {...props}
                                        />
                                      );
                                    }
                                    return <img src={src} alt={alt} className="max-w-full rounded-xl my-2" {...props} />;
                                  }
                                }}
                              >
                                {maskUnclosedLatex(streamingContent)}
                              </ReactMarkdown>
                              <span className="inline-block w-0.5 h-4 bg-[var(--acc)] ml-0.5 animate-pulse align-middle" />
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Thinking Loader — Advanced Neural Style */}
                  <AnimatePresence>
                    {isThinking && !streamingContent && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, transition: { duration: 0.2 } }}
                        className="flex items-start gap-6 px-1 py-6 w-full"
                        aria-live="polite"
                        aria-busy="true"
                      >
                        <div className="w-9 h-9 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <NeuralNode />
                        </div>
                        <div className="flex flex-col gap-2.5 flex-1">
                          <div className="flex items-center gap-3">
                            <span className="text-[12px] font-semibold uppercase tracking-wider text-[var(--accent)]/60">Neural_Synthesis</span>
                            <ThinkingDots />
                          </div>
                          <SkeletonLoader />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                  <div ref={chatEndRef} className="h-4" />
                </>
              )}
            </div>
          </div>

          {/* Input bar — floating at bottom */}
          <div className="absolute bottom-0 left-0 w-full z-10" style={{
            padding: '0 0 16px 0',
            background: 'var(--bg-base)',
          }}>
            <InputDock onOpenProject={() => setIsProjectOpen(true)} />
          </div>
        </main>

        {/* Right panel — Live2D + stats */}
        <DashboardStats
          bridgeStatus={bridgeStatus}
          isThinking={isThinking}
          isTalking={isTalking}
          currentEmotion={currentEmotion}
          avatarScale={avatarScale}
          setAvatarScale={setAvatarScale}
          amplitude={amplitude}
          chemicals={chemicals}
        />
      </div>

      {/* Modals */}
      <SettingsPanel 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
        onSave={() => {
          // Tell Python to reload user_settings.json instantly
          const { reloadConfig } = useNeuralStore.getState();
          reloadConfig();
        }}
      />
      <ProjectIntelligence isOpen={isProjectOpen} onClose={() => setIsProjectOpen(false)} />

      {isPurgeConfirmOpen && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md" role="dialog" aria-modal="true" aria-labelledby="purge-title">
          <div className="glass-pane rounded-[32px] p-10 max-w-sm w-full mx-4 text-center">
            <AlertTriangle className="mx-auto text-red-400 mb-4" size={32} />
            <h2 id="purge-title" className="text-[14px] font-semibold text-[#f0ebe3] mb-4">Initialize Purge?</h2>
            <p className="text-[13px] text-[#9a8f7e] leading-relaxed mb-8">Reset current session state.</p>
            <div className="flex gap-4">
              <button onClick={() => setIsPurgeConfirmOpen(false)}
                className="flex-1 py-3 rounded-xl bg-white/[0.03] border border-white/5 text-[13px] font-medium text-[#9a8f7e] hover:bg-white/5 hover:text-[#f0ebe3] transition-all">
                Cancel
              </button>
              <button onClick={async () => { setIsPurgeConfirmOpen(false); await triggerPurge(); }}
                className="flex-1 py-3 rounded-xl bg-[#f87171]/20 border border-[#f87171]/30 text-[13px] font-medium text-[#f87171] hover:bg-[#f87171]/30 transition-all">
                Proceed
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </>
  );
}

function NeuralNode() {
  return (
    <div className="relative w-6 h-6">
      <div className="absolute inset-0 bg-[var(--accent)]/20 blur-[6px] rounded-full animate-pulse" />
      <div className="relative w-full h-full rounded-full border border-[var(--accent)]/40 flex items-center justify-center">
        <div className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full" />
      </div>
    </div>
  );
}

function ThinkingDots() {
  return (
    <div className="flex gap-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          animate={{ scale: [1, 1.5, 1], opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
          className="w-1 h-1 rounded-full bg-[var(--accent)]"
        />
      ))}
    </div>
  );
}

export default function AppWithErrorBoundary() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );
}
