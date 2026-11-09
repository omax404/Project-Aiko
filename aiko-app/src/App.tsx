import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { emit } from '@tauri-apps/api/event';
import { Sidebar } from './components/Sidebar';
import { OnboardingWizard } from './components/OnboardingWizard';
import { ChatBubble } from './components/ChatBubble';
import { InputDock } from './components/InputDock';
import { SettingsPanel } from './components/SettingsPanel';
import { DiagnosticsScreen } from './components/DiagnosticsScreen';
import { SkeletonLoader } from './components/SkeletonLoader';
import { ProjectIntelligence } from './components/ProjectIntelligence';
import { ErrorBoundary } from './components/ErrorBoundary';
import { announce, ScreenReaderAnnouncer } from './components/ScreenReaderAnnouncer';
import { SkipLink } from './components/SkipLink';
import { useNeuralStore, getHubUrl } from './store/useNeuralStore';
import { useShallow } from 'zustand/react/shallow';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { Zap, AlertTriangle, Sparkles } from 'lucide-react';
import { TitleBar } from './components/ui/TitleBar';
import { DashboardStats } from './components/ui/DashboardStats';
import { WelcomeScreen } from './components/ui/WelcomeScreen';
import { NeuralNode } from './components/ui/NeuralNode';
import { ThinkingDots } from './components/ui/ThinkingDots';
import { Live2DAvatar } from './components/Live2DAvatar';
import { AmbientParticlesCanvas } from './components/ui/AmbientParticlesCanvas';
import { useStageBackground, stageBgCss, resolveStageMediaUrl, moodAmbientCss } from './stageBackground';
import { DraggableAvatar } from './components/DraggableAvatar';

function extractHtmlCode(text: string): string | null {
  const match = text.match(/```html([\s\S]*?)(?:```|$)/i);
  return match?.[1] ? match[1].trim() : null;
}

/* ── Main App ────────────────────────────────────────────── */
function App() {
  // Note: `amplitude` is intentionally excluded from this top-level store hook.
  // Consuming 30-60Hz audio amplitude here would trigger full viewport re-renders.
  // Instead, it is scoped exclusively inside DashboardStats.tsx for the avatar canvas.
  const {
    messages, streamingContent, connect, activeSessionId, sessions,
    isThinking, triggerPurge, loadSessions, fetchBridgeStatus, fetchSettings,
    bridgeStatus, currentEmotion, isSidebarOpen, toggleSidebar, themeColor,
    dynamicsIntensity, showAnimatedAssets, isTalking, avatarScale, setAvatarScale,
    layoutMode,
    apiConfig, chemicals, pendingToolRequest, respondToToolRequest
  } = useNeuralStore(useShallow((state) => ({
    messages: state.messages,
    streamingContent: state.streamingContent,
    connect: state.connect,
    activeSessionId: state.activeSessionId,
    sessions: state.sessions,
    isThinking: state.isThinking,
    triggerPurge: state.triggerPurge,
    loadSessions: state.loadSessions,
    fetchBridgeStatus: state.fetchBridgeStatus,
    fetchSettings: state.fetchSettings,
    bridgeStatus: state.bridgeStatus,
    currentEmotion: state.currentEmotion,
    isSidebarOpen: state.isSidebarOpen,
    toggleSidebar: state.toggleSidebar,
    themeColor: state.themeColor,
    dynamicsIntensity: state.dynamicsIntensity,
    showAnimatedAssets: state.showAnimatedAssets,
    isTalking: state.isTalking,
    avatarScale: state.avatarScale,
    setAvatarScale: state.setAvatarScale,
    layoutMode: state.layoutMode,
    apiConfig: state.apiConfig,
    chemicals: state.chemicals,
    pendingToolRequest: state.pendingToolRequest,
    respondToToolRequest: state.respondToToolRequest
  })));

  const stageBg = useStageBackground();
  const [activeArtifactCode, setActiveArtifactCode] = useState<string | null>(null);
  const [settingsLoaded, setSettingsLoaded] = useState(false);

  useEffect(() => {
    if (streamingContent) {
      const code = extractHtmlCode(streamingContent);
      if (code) {
        setActiveArtifactCode(code);
      }
    } else {
      const lastAiMsg = [...messages].reverse().find(
        (m: any) => m.role === 'assistant' && /```html[\s\S]*?/i.test(m.content)
      );
      if (lastAiMsg) {
        setActiveArtifactCode(extractHtmlCode(lastAiMsg.content));
      } else {
        setActiveArtifactCode(null);
      }
    }
  }, [messages, streamingContent]);

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

  const activeSession = (sessions || []).find(s => s.id === activeSessionId);
  const sessionLabel = activeSession?.title || 'New chat';
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState(false);
  const [isProjectOpen, setIsProjectOpen] = useState(false);
  const [isPurgeConfirmOpen, setIsPurgeConfirmOpen] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    emit('app-ready').catch(() => { });
    // Inject accent color on mount
    document.documentElement.style.setProperty('--acc', themeColor);
    document.documentElement.style.setProperty('--accent', themeColor);
    document.documentElement.style.setProperty('--acc2', themeColor);
    document.documentElement.style.setProperty('--acc-soft', `${themeColor}1f`);
    document.documentElement.style.setProperty('--acc-glow', `${themeColor}40`);

    try { connect(getHubUrl()); } catch (e) { }
    fetchSettings().finally(() => setSettingsLoaded(true));
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
      if (lastMsg && lastMsg.role === 'assistant') {
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
        if (isDiagnosticsOpen) setIsDiagnosticsOpen(false);
        if (isProjectOpen) setIsProjectOpen(false);
        if (isPurgeConfirmOpen) setIsPurgeConfirmOpen(false);
      }
      // Ctrl+Shift+D toggles diagnostics
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'D' || e.key === 'd')) {
        e.preventDefault();
        setIsDiagnosticsOpen((prev) => !prev);
      }
      // F1 toggles sidebar
      if (e.key === 'F1') {
        e.preventDefault();
        toggleSidebar();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSettingsOpen, isDiagnosticsOpen, isProjectOpen, isPurgeConfirmOpen, toggleSidebar]);

  const [isDraggingFile, setIsDraggingFile] = useState(false);
  const uploadFile = useNeuralStore((s) => s.uploadFile);
  const sendMessage = useNeuralStore((s) => s.sendMessage);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDraggingFile) setIsDraggingFile(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // Only set to false if leaving the window
    if (e.clientX <= 0 || e.clientY <= 0 || e.clientX >= window.innerWidth || e.clientY >= window.innerHeight) {
      setIsDraggingFile(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingFile(false);

    const files = e.dataTransfer.files;
    if (!files || files.length === 0) return;

    const uploadedUrls: string[] = [];
    for (const file of Array.from(files)) {
      try {
        const res = await uploadFile(file);
        if (res && res.url) uploadedUrls.push(res.url);
      } catch (err) {
        console.error("Dropzone upload failed:", err);
      }
    }

    if (uploadedUrls.length > 0) {
      sendMessage("Analyze these attachments for me, Aiko.", uploadedUrls);
    }
  };

  return (
    <>
      <SkipLink targetId="main-content" />
      <ScreenReaderAnnouncer />
      <div 
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`aiko-app-shell${activeArtifactCode ? ' has-artifact' : ''}`}
        style={{
          width: '100%', height: '100dvh', minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column',
          overflow: 'hidden', background: 'var(--bg-base)', color: 'var(--t1)',
          borderRadius: '24px', border: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: '0 15px 35px rgba(0, 0, 0, 0.6)', position: 'relative'
        }}
      >
        {/* Full-Screen Drag and Drop Overlay */}
        <AnimatePresence>
          {isDraggingFile && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 z-[150] flex flex-col items-center justify-center bg-[#0B060F]/85 backdrop-blur-xl border-2 border-dashed border-[var(--acc)] rounded-[24px] pointer-events-none"
            >
              <div className="flex flex-col items-center gap-4 p-8 rounded-3xl bg-white/[0.03] border border-white/10 shadow-2xl">
                <Zap size={48} className="text-[var(--acc)] animate-bounce" />
                <p className="text-lg font-semibold text-[#f0ebe3] tracking-wide">
                  Drop file to analyze with Aiko
                </p>
                <p className="text-xs text-[var(--acc)] opacity-80 uppercase tracking-widest">
                  Images • Code Snippets • Documents
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      {/* ONE titlebar — session name + action icons + window controls */}
      <TitleBar
        sessionLabel={sessionLabel}
        showAnimatedAssets={showAnimatedAssets}
        onSettings={() => setIsSettingsOpen(true)}
        onToggleSidebar={toggleSidebar}
        onOpenDiagnostics={() => setIsDiagnosticsOpen(true)}
      />

      {/* Onboarding Overlay */}
      {(settingsLoaded && !apiConfig.apiKey && apiConfig.provider !== 'Ollama') && (
        <div className="absolute inset-0 z-[100]">
          <OnboardingWizard />
        </div>
      )}

      {/* Body row */}
      <div className="aiko-workspace-row" style={{ display: 'flex', flex: 1, overflow: 'hidden', minHeight: 0 }}>

        {/* Left sidebar — animated collapse */}
        <AnimatePresence initial={false}>
          {isSidebarOpen && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 240, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{
                type: 'spring',
                damping: 20 + (dynamicsIntensity / 10),
                stiffness: 100 + (dynamicsIntensity / 2)
              }}
              className="aiko-sidebar-shell"
              style={{ overflow: 'hidden', flexShrink: 0 }}
            >
              <Sidebar onOpenSettings={() => setIsSettingsOpen(true)} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Dual pane container */}
        <div className="aiko-main-panes flex-1 flex overflow-hidden">
          {layoutMode === 'cinematic' ? (
            /* ── Cinematic 70:30 Hero Ratio (OpenAmika Style) ── */
            <div className="flex-1 flex w-full h-full overflow-hidden">
              {/* Left Stage (68-70% width): Live2D Companion Hero */}
              <div
                className="relative flex-1 h-full overflow-hidden flex flex-col items-center justify-center select-none"
                style={{
                  background: stageBgCss(stageBg),
                }}
              >
                {/* Custom picture / animated GIF background (chosen in Settings > Appearance) */}
                {stageBg.mode === 'image' && stageBg.image && (
                  <>
                    <div
                      className="absolute inset-0 pointer-events-none"
                      style={{
                        backgroundImage: `url(${resolveStageMediaUrl(stageBg.image)})`,
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                        filter: stageBg.blur ? `blur(${stageBg.blur}px)` : undefined,
                        transform: stageBg.blur ? 'scale(1.08)' : undefined,
                      }}
                    />
                    <div
                      className="absolute inset-0 pointer-events-none"
                      style={{ background: `rgba(0, 0, 0, ${stageBg.dim / 100})` }}
                    />
                  </>
                )}

                {/* Custom video background (.mp4 / .webm / .mov) */}
                {stageBg.mode === 'video' && stageBg.video && (
                  <>
                    <video
                      src={resolveStageMediaUrl(stageBg.video)}
                      autoPlay
                      loop
                      muted
                      playsInline
                      className="absolute inset-0 w-full h-full object-cover pointer-events-none"
                      style={{
                        filter: stageBg.blur ? `blur(${stageBg.blur}px)` : undefined,
                        transform: stageBg.blur ? 'scale(1.08)' : undefined,
                      }}
                    />
                    <div
                      className="absolute inset-0 pointer-events-none"
                      style={{ background: `rgba(0, 0, 0, ${stageBg.dim / 100})` }}
                    />
                  </>
                )}

                {/* Mood-Reactive Ambient Aura (shifts with Aiko's current emotion) */}
                {moodAmbientCss(currentEmotion, stageBg.moodReactive) && (
                  <div
                    className="absolute inset-0 pointer-events-none transition-all duration-1000"
                    style={{
                      background: moodAmbientCss(currentEmotion, stageBg.moodReactive) || undefined,
                    }}
                  />
                )}

                {/* Subtle stardust particles floating in cosmic backdrop */}
                <AmbientParticlesCanvas />

                {/* Floating companion status pill */}
                <div className="absolute top-4 left-5 z-10 flex items-center gap-2 rounded-full border border-white/10 bg-black/40 px-3.5 py-1.5 backdrop-blur-md shadow-lg shadow-black/40">
                  <span
                    className="h-2 w-2 rounded-full animate-pulse"
                    style={{
                      background: bridgeStatus?.status === 'connected' ? 'var(--accent)' : '#a1a1aa',
                      boxShadow: bridgeStatus?.status === 'connected' ? '0 0 10px var(--accent)' : 'none',
                    }}
                  />
                  <span className="text-xs font-semibold text-white/90 tracking-wide">
                    {bridgeStatus?.status === 'connected' ? 'Aiko Active' : 'Connecting...'}
                  </span>
                  <span className="text-[10px] text-white/40 font-mono">
                    {isThinking ? '· thinking' : isTalking ? '· speaking' : `· ${currentEmotion}`}
                  </span>
                </div>

                {/* Live2D Avatar Canvas - Large Cinematic Render */}
                <div className="relative z-10 w-full h-full flex items-center justify-center overflow-hidden">
                  {/* Size/position chosen in Settings > Appearance */}
                  <DraggableAvatar>
                  <Live2DAvatar
                    modelUrl="/live2d/vivian/vivian.model3.json"
                    isThinking={isThinking}
                    isTalking={isTalking}
                    emotion={currentEmotion}
                    width={800}
                    height={900}
                    scale={Math.min(avatarScale * 1.35, 1.6)}
                    chemicals={chemicals}
                    interactive
                  />
                  </DraggableAvatar>
                </div>

                {/* Bottom atmospheric dark fog vignette */}
                <div
                  className="pointer-events-none absolute inset-x-0 bottom-0 h-40 z-10"
                  style={{
                    background: 'linear-gradient(to top, rgba(13, 10, 20, 0.95) 0%, rgba(13, 10, 20, 0.4) 50%, transparent 100%)',
                  }}
                />
              </div>

              {/* Right Column (30-32% width): Chat & Voice Stream */}
              <aside
                aria-label="Conversation panel"
                className="w-[380px] lg:w-[440px] xl:w-[480px] shrink-0 h-full flex flex-col border-l border-white/[0.08] bg-[#120e1a]/95 backdrop-blur-xl relative z-20"
              >
                {/* Header message */}
                <div className="px-6 pt-5 pb-3 border-b border-white/[0.05] text-center select-none">
                  <h2 className="text-sm font-bold text-white tracking-wide">Say hi to Aiko</h2>
                  <p className="mt-1 text-xs text-white/45">Type a message below, or tap the mic and just talk.</p>
                </div>

                {/* Vertical Message Stream */}
                <div className="relative flex-1 overflow-y-auto px-5 py-4 custom-scrollbar space-y-4">
                  {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center p-5 text-white/40">
                      <Sparkles size={24} className="text-[var(--accent)]/60 mb-2.5" />
                      <p className="text-xs font-semibold text-white/80">Ready when you are</p>
                      <p className="text-[11px] text-white/45 mt-1 max-w-[260px]">
                        Drop a course PDF, ask Aiko to help on your PC, or start a daily study / recap session:
                      </p>
                      <div className="mt-4 grid grid-cols-2 gap-2 w-full max-w-[320px] text-left">
                        {[
                          {
                            badge: '📚 Study Mode',
                            title: 'Quiz & Flashcards',
                            prompt: 'Enter Study Mode: quiz me on my current topic with 5 active-recall questions and create concise flashcards for what I miss.',
                          },
                          {
                            badge: '🖥️ PC Helper',
                            title: 'Check My Screen',
                            prompt: 'Look at my screen and summarize what I am working on right now, plus suggest the next step.',
                          },
                          {
                            badge: '🌙 Daily Recap',
                            title: 'Evening Summary',
                            prompt: 'Give me a short evening recap of what we worked on today and help me plan my top 3 priorities for tomorrow.',
                          },
                          {
                            badge: '🎨 Customize',
                            title: 'Background & Persona',
                            action: () => setIsSettingsOpen(true),
                          },
                        ].map((chip) => (
                          <button
                            key={chip.badge}
                            type="button"
                            onClick={() => (chip.action ? chip.action() : sendMessage(chip.prompt!))}
                            className="flex flex-col gap-0.5 p-2.5 rounded-xl border border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.07] hover:border-[var(--accent)]/40 transition-all cursor-pointer text-left"
                          >
                            <span className="text-[10px] font-semibold text-[var(--accent)]">{chip.badge}</span>
                            <span className="text-[11.5px] font-medium text-white/85">{chip.title}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <>
                      <AnimatePresence mode="popLayout" initial={false}>
                        {messages.map((msg: any, i: number) => (
                          <ChatBubble
                            key={(msg.id || msg.timestamp || 'msg') + '-' + i}
                            id={msg.id}
                            role={msg.role}
                            content={msg.content}
                            emotion={msg.emotion}
                            timestamp={msg.timestamp}
                            attachments={msg.attachments}
                          />
                        ))}
                      </AnimatePresence>

                      {/* Streaming bubble */}
                      <AnimatePresence>
                        {streamingContent && (
                          <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex w-full">
                            <div className="flex gap-3 max-w-[95%]">
                              <div className="w-7 h-7 rounded-lg bg-[var(--acc)]/15 border border-[var(--acc)]/30 flex items-center justify-center shrink-0 mt-0.5">
                                <Zap size={13} className="text-[var(--acc)] animate-pulse" />
                              </div>
                              <div className="flex flex-col gap-1 min-w-0">
                                <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--acc)]">Aiko</span>
                                <div className="text-[13px] leading-relaxed text-white/90 selectable markdown-content">
                                  <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]}>
                                    {maskUnclosedLatex(streamingContent)}
                                  </ReactMarkdown>
                                  <span className="inline-block w-1.5 h-3.5 bg-[var(--acc)] ml-1 animate-pulse align-middle" />
                                </div>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>

                      {/* Thinking Loader */}
                      <AnimatePresence>
                        {isThinking && !streamingContent && (
                          <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex items-center gap-3 py-2 text-white/60">
                            <NeuralNode />
                            <span className="text-xs font-medium tracking-wide">Aiko is thinking...</span>
                            <ThinkingDots />
                          </motion.div>
                        )}
                      </AnimatePresence>

                      <div ref={chatEndRef} className="h-2" />
                    </>
                  )}
                </div>

                {/* Bottom Input Dock with hands-free caption */}
                <div className="p-3 border-t border-white/[0.06] bg-black/30 backdrop-blur-md">
                  <InputDock />
                  <p className="mt-2 text-center text-[10px] text-white/35 select-none">
                    Tap the mic to talk hands-free, or hold it down for push-to-talk.
                  </p>
                </div>
              </aside>
            </div>
          ) : (
            /* ── Classic Chat Focus Layout ── */
            <motion.div
              animate={{
                width: activeArtifactCode ? '42%' : '100%'
              }}
              transition={{
                type: 'spring',
                damping: 25,
                stiffness: 120
              }}
              className="h-full flex overflow-hidden border-r border-white/[0.04]"
              style={{ flex: '0 0 auto', minWidth: 0, flexShrink: 1 }}
            >
              {/* Chat area */}
              <main
                id="main-content"
                tabIndex={-1}
                aria-label="Chat conversation"
                style={{
                  flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative',
                  background: 'var(--bg-base)'
                }}
                className="group/chat"
              >
                {/* Messages */}
                <div className="relative z-10 flex-1 overflow-y-auto custom-scrollbar" style={{ padding: '24px 24px 0' }}>
                  <div style={{ maxWidth: 680, margin: '0 auto', display: 'flex', flexDirection: 'column', paddingBottom: 160 }}>
                    {messages.length === 0 ? (
                      <WelcomeScreen
                        onRecall={async () => {
                          await loadSessions();
                          if (!isSidebarOpen) toggleSidebar();
                        }}
                        onStartPrompt={sendMessage}
                      />
                    ) : (
                      <>
                        <AnimatePresence mode="popLayout" initial={false}>
                          {messages.map((msg: any, i: number) => (
                            <ChatBubble
                              key={(msg.id || msg.timestamp || 'msg') + '-' + i}
                              id={msg.id} role={msg.role} content={msg.content}
                              emotion={msg.emotion} timestamp={msg.timestamp}
                              attachments={msg.attachments}
                            />
                          ))}
                        </AnimatePresence>

                        {/* Streaming bubble */}
                        <AnimatePresence>
                          {streamingContent && (
                            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                              className="flex w-full mb-12">
                              <div className="flex gap-6 max-w-[85%]">
                                <div className="w-9 h-9 rounded-xl bg-[var(--acc)]/10 border border-[var(--acc)]/30 shadow-accent-glow flex items-center justify-center flex-shrink-0 mt-1">
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
                                          const hubUrl = getHubUrl();
                                          const absoluteSrc = src.startsWith('http') || src.startsWith('data:') ? src : `${hubUrl}${src}`;
                                          
                                          const isSticker = src.includes('/stickers/') && !src.includes('selfie') && !src.includes('gen_');
                                          if (isSticker) {
                                            return (
                                              <img 
                                                src={absoluteSrc} 
                                                alt={alt || "sticker"} 
                                                className="w-28 h-28 object-contain my-2 inline-block transition-transform hover:scale-110 duration-200 cursor-pointer drop-shadow-[0_4px_12px_rgba(0,0,0,0.15)]"
                                                {...props}
                                              />
                                            );
                                          }
                                          return <img src={absoluteSrc} alt={alt} className="max-w-[320px] max-h-[480px] rounded-xl my-2 object-cover shadow-lg border border-white/10" {...props} />;
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
                <div className="absolute bottom-0 left-0 w-full z-20 pointer-events-none" style={{
                  padding: '0 0 16px 0',
                  background: 'linear-gradient(to top, var(--bg-base) 85%, transparent)',
                }}>
                  <div className="pointer-events-auto">
                    <InputDock />
                  </div>
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
                chemicals={chemicals}
                isCompact={!!activeArtifactCode}
              />
            </motion.div>
          )}

          <AnimatePresence>
            {activeArtifactCode && (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: '58%', opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{
                  type: 'spring',
                  damping: 25,
                  stiffness: 120
                }}
                className="aiko-artifact-pane h-full flex flex-col bg-[#141211] overflow-hidden"
              >
                {/* Minimalist Dark Header */}
                <div className="h-10 px-4 bg-[#0e0d0c] border-b border-white/[0.04] flex items-center justify-between shrink-0 select-none">
                  <span className="text-[11px] font-bold tracking-widest text-[var(--acc)] uppercase">
                    Neural Artifact Preview
                  </span>
                  <button
                    onClick={() => setActiveArtifactCode(null)}
                    className="text-[#5a5248] hover:text-[var(--acc)] transition-colors text-[10px] uppercase font-bold tracking-wider"
                    title="Close preview"
                  >
                    Close
                  </button>
                </div>

                {/* Sandbox iframe */}
                <div className="flex-1 bg-white relative">
                  <iframe
                    title="Artifact Simulation"
                    sandbox="allow-scripts"
                    srcDoc={activeArtifactCode}
                    className="w-full h-full border-none bg-white"
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Modals */}
      <SettingsPanel 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
        onOpenDiagnostics={() => setIsDiagnosticsOpen(true)}
        onSave={() => {
          // Tell Python to reload user_settings.json instantly
          const { reloadConfig } = useNeuralStore.getState();
          reloadConfig();
        }}
      />
      <DiagnosticsScreen
        isOpen={isDiagnosticsOpen}
        onClose={() => setIsDiagnosticsOpen(false)}
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
      {pendingToolRequest && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md" role="dialog" aria-modal="true" aria-labelledby="tool-title">
          <div className="glass-pane rounded-[32px] p-10 max-w-sm w-full mx-4 text-center">
            <Zap className="mx-auto text-[var(--acc)] mb-4 animate-pulse" size={32} />
            <h2 id="tool-title" className="text-[14px] font-semibold text-[#f0ebe3] mb-2 uppercase tracking-widest">Aiko Requests Control</h2>
            <div className="text-[13px] text-[#9a8f7e] leading-relaxed mb-6">
              Aiko wants to execute tool <strong className="text-[var(--acc)]">{pendingToolRequest.toolName}</strong> with arguments:
              <pre className="mt-3 p-3 bg-white/[0.02] border border-white/5 rounded-lg text-left text-[11px] font-mono text-[#c9c5bd] overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(pendingToolRequest.args, null, 2)}
              </pre>
            </div>
            <div className="flex gap-4">
              <button onClick={() => respondToToolRequest(pendingToolRequest.requestId, false)}
                className="flex-1 py-3 rounded-xl bg-white/[0.03] border border-white/5 text-[13px] font-medium text-[#9a8f7e] hover:bg-white/5 hover:text-[#f0ebe3] transition-all">
                Deny
              </button>
              <button onClick={() => respondToToolRequest(pendingToolRequest.requestId, true)}
                className="flex-1 py-3 rounded-xl bg-[var(--acc)]/20 border border-[var(--acc)]/30 text-[13px] font-medium text-[var(--acc)] hover:bg-[var(--acc)]/30 transition-all">
                Allow
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </>
  );
}

export default function AppWithErrorBoundary() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );
}
