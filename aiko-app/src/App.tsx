import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { emit } from '@tauri-apps/api/event';
import { Sidebar } from './components/Sidebar';
import { OnboardingWizard } from './components/OnboardingWizard';
import { ChatBubble } from './components/ChatBubble';
import { InputDock } from './components/InputDock';
import { SettingsPanel } from './components/SettingsPanel';
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
import { Zap, AlertTriangle } from 'lucide-react';
import { TitleBar } from './components/ui/TitleBar';
import { DashboardStats } from './components/ui/DashboardStats';
import { WelcomeScreen } from './components/ui/WelcomeScreen';
import { NeuralNode } from './components/ui/NeuralNode';
import { ThinkingDots } from './components/ui/ThinkingDots';
function extractHtmlCode(text: string): string | null {
  const match = text.match(/```html([\s\S]*?)(?:```|$)/i);
  return match ? match[1].trim() : null;
}

/* ── Main App ────────────────────────────────────────────── */
function App() {
  const {
    messages, streamingContent, connect, activeSessionId, sessions,
    isThinking, triggerPurge, loadSessions, fetchBridgeStatus, fetchSettings,
    bridgeStatus, currentEmotion, isSidebarOpen, toggleSidebar, themeColor,
    dynamicsIntensity, showAnimatedAssets, isTalking, avatarScale, setAvatarScale,
    amplitude, apiConfig, chemicals, pendingToolRequest, respondToToolRequest
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
    amplitude: state.amplitude,
    apiConfig: state.apiConfig,
    chemicals: state.chemicals,
    pendingToolRequest: state.pendingToolRequest,
    respondToToolRequest: state.respondToToolRequest
  })));

  const [activeArtifactCode, setActiveArtifactCode] = useState<string | null>(null);

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
    document.documentElement.style.setProperty('--accent', themeColor);
    document.documentElement.style.setProperty('--acc2', themeColor);
    document.documentElement.style.setProperty('--acc-soft', `${themeColor}1f`);
    document.documentElement.style.setProperty('--acc-glow', `${themeColor}40`);

    try { connect(getHubUrl()); } catch (e) { }
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
              <Sidebar onOpenSettings={() => setIsSettingsOpen(true)} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Dual pane container */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Panel: houses the current Live2D avatar/Gothic-cyberpunk chat UI */}
          <motion.div
            animate={{
              width: activeArtifactCode ? '40%' : '100%'
            }}
            transition={{
              type: 'spring',
              damping: 25,
              stiffness: 120
            }}
            className="h-full flex overflow-hidden border-r border-white/[0.04]"
            style={{ flexShrink: 0 }}
          >
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
              <div className="absolute bottom-0 left-0 w-full z-10" style={{
                padding: '0 0 16px 0',
                background: 'var(--bg-base)',
              }}>
                <InputDock />
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
              isCompact={!!activeArtifactCode}
            />
          </motion.div>

          <AnimatePresence>
            {activeArtifactCode && (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: '60%', opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{
                  type: 'spring',
                  damping: 25,
                  stiffness: 120
                }}
                className="h-full flex flex-col bg-[#141211] overflow-hidden"
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
